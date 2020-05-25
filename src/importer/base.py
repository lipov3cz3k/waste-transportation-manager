from database import init_db, db_session
from common.service_base import ServiceBase
from common.utils import get_tqdm
from logging import getLogger
logger = getLogger(__name__)

class Importer(ServiceBase):
    def __init__(self):
        ServiceBase.__init__(self)
        self.source = None
        self.workbook = None
        self.db_session = None

    def RemoveDBSession(self):
        if self.db_session:
            self.db_session.remove()

    def Import(self):
        init_db()
        self.db_session = db_session
        ("start import %s" % self.source)
        
    def SaveAllRecordsToDatabase(self, records):
        logger.info("Saving records to database")
        self.db_session.add_all(records)
        self.db_session.commit()

    def LoadOSMLocation(self, city_filter=None):
        logger.info("Start reversing Addresses.")
        addresses_without_location = self._GetAddressesWithoutLocation(city_filter=city_filter)
        self._GetLocationsForAddresses(addresses_without_location)

    def _GetAddressesWithoutLocation(self, city_filter=None):
        from models.location import Address

        addresses_obj = self.db_session.query(Address).filter(Address.location == None)
        if city_filter is not None:
            addresses_obj= addresses_obj.filter(Address.city.like(city_filter))
        addresses_obj = addresses_obj.all()
        return addresses_obj

    def _GetLocationsForAddresses(self, addresses_array):
        from time import sleep
        from geopy.geocoders import Nominatim
        from geopy.exc import GeocoderTimedOut
        from models.location import OSMLocation
        logger.info("Getting locations for Addresses <%d> (use Nominatim)" % len(addresses_array))

        # geolocator = Nominatim(user_agent="wtm", domain="localhost:7070", scheme="http", timeout=60)
        geolocator = Nominatim(user_agent="wtm", timeout=60)
        for addr_obj in get_tqdm(addresses_array, self.SetState, desc="getting locations", total=None):
            #print("getting new by nominatim ...", LogType.trace, only_Message=True)
            successful = False
            while not successful:
                location = self.db_session.query(OSMLocation).filter(OSMLocation.road == addr_obj.street,
                                                                     OSMLocation.house_number == addr_obj.house_number,
                                                                     ((OSMLocation.city == addr_obj.city) | (OSMLocation.town == addr_obj.city))).first()
                if location:
                    osm_id=location.osm_id
                    address = []
                    successful = True
                else:
                    try:
                        query = {'street':''}
                        if addr_obj.house_number:
                            query['street'] = addr_obj.house_number
                        if addr_obj.street:
                            if query['street']:
                                query['street'] += ' '
                            query['street'] += addr_obj.street
                        if addr_obj.city:
                            query['city'] = addr_obj.city
                        if addr_obj.postal:
                            query['postal'] = addr_obj.postal
                        if addr_obj.country:
                            query['country'] = addr_obj.country
                        location = geolocator.geocode(query,
                                                      addressdetails=True)
                    except GeocoderTimedOut as e:
                        print("Service timed out, waiting a little bit")
                        sleep(10)
                    except Exception as e:
                        raise e
                    else:
                        successful = True
                    if location == None:
                        continue
                    address = location.raw['address']
                    osm_id = location.raw['osm_id']
                    sleep(1)
                location_obj = OSMLocation.as_unique(self.db_session,
                                                  address=address, 
                                                  osm_id=osm_id, 
                                                  latitude=location.latitude, 
                                                  longitude=location.longitude)
                addr_obj.set_location(location_obj)
                self.db_session.commit()
