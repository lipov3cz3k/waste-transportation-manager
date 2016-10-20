from openpyxl import load_workbook
from common.utils import get_tqdm

class Importer:
    def __init__(self):
        self.state = {}
        self.SetState(action="init", percentage=0)
        self.source = None
        self.workbook = None
        self.run = False
        self.db_session = None

    def RemoveDBSession(self):
        if self.db_session:
            self.db_session.remove()

    def SetState(self, action = None, percentage = None):
        if action != None:
            self.state['action'] = action
        if percentage != None:
            self.state['percentage'] = int(percentage)

    def TestIsRun(self):
        if not self.run:
            raise Exception("Service not running")

    def Import(self, filename):
        from database import init_db, db_session
        init_db()
        self.db_session = db_session

        self.run = True # TODO: Move to run method

        print("start import from xlsx")
        self.workbook = load_workbook(filename, read_only = True)
        
    def SaveRecordToDatabase(self, rec_obj):
        #print("Save DOC object to database (%s)" % basename(rec_obj.file_name), LogType.trace)

        self.db_session.add(rec_obj)
        self.db_session.commit()       

    def SaveAllRecordsToDatabase(self, records):
        print("Saving records to database")#), LogType.trace)
        self.db_session.add_all(records)
        self.db_session.commit()


    def GetAddressesWithoutLocation(self):
        from models.location import Address

        addresses_obj = self.db_session.query(Address).filter(Address.location == None).all()
        return addresses_obj

    def GetLocationsForAddresses(self, addresses_array):
        from time import sleep
        from geopy.geocoders import Nominatim
        from models.location import Location
        print("Getting locations for Addresses <%d> (use Nominatim)" % len(addresses_array))#, LogType.trace)

        geolocator = Nominatim()
        for addr_obj in get_tqdm(addresses_array, self.SetState, desc="getting locations", total=None):
            #print("getting new by nominatim ...", LogType.trace, only_Message=True)
            successful = False
            while not successful:
                try:
                    location = geolocator.geocode({'street':addr_obj.house_number + ' ' + addr_obj.street,'city':addr_obj.city},
                                                  addressdetails=True)
                except Exception as e:
                    raise e
                else:
                    successful = True
                if location == None:
                    continue
                address = location.raw['address']
                osm_id = location.raw['osm_id']
                location_obj = Location.as_unique(self.db_session,
                                                  address=address, 
                                                  osm_id=osm_id, 
                                                  latitude=location.latitude, 
                                                  longitude=location.longitude)
                addr_obj.set_location(location_obj)
                self.db_session.commit()
                sleep(1)


class Cheb(Importer):
    def __init__(self):
        super().__init__()
        self.source = "Cheb"

    def Import(self, filename):
        from models.waste import Cheb
        super().Import(filename)

        normalize = {'Typ kontejneru' : 'container_type',
                     'Interval' : 'interval',
                     'Kód odpadu' : 'waste_code',
                     'Název odpadu' : 'waste_name',
                     '#TECH_GRP#' : 'tech_grp',
                     'Počet ks' : 'quantity',
                     'MJ' : 'quantity_unit',
                     'Zahájení' : 'start',
                     'Ukončení' : 'end',
                     'Stav' : 'state',
                     'Fakturovat' : 'invoicing',
                     'V trase' : 'in_route',
                     'Město' : 'city',
                     'Ulice' : 'street',
                     'č. p.' : 'house_number',
                     'Jméno a příjmení' : 'name',
                     'Poznámka pro dispečera' : 'dispatcher_note',
                     'Poznámka do faktury' : 'invoice_note',
                     'Poznámka' : 'note',
                     'Den svozu' : 'days',
                     'POZNÁMKY PRO OPRAVY' : 'fix_note',
                     'Řádek' : 'row',
                     'Pořadí' : 'order'}

        #load values from xls
        data = []
        for sheet in self.workbook:            
            rows = sheet.rows
            first_row = [cell.value for cell in next(rows)]
            for row in get_tqdm(rows, self.SetState, desc="loading " + sheet.title, total=sheet.max_row):
                record = { 'waste_type': sheet.title }
                for key, cell in zip(first_row, row):
                    if cell.data_type == 's':
                        record[normalize.get(key, key)] = cell.value.strip()
                    else:
                        record[normalize.get(key, key)] = cell.value
                data.append(Cheb(self.db_session, record))

            #save to database
            self.SaveAllRecordsToDatabase(data)
            data.clear()

        #get location
        #print("Start reversing Addresses.")#, LogType.info)
        #addresses_without_location = self.GetAddressesWithoutLocation()
        #self.GetLocationsForAddresses(addresses_without_location)
