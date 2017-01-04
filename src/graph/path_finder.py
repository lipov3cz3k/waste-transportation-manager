from openpyxl import load_workbook
from common.utils import LogType, print, get_tqdm
from waste.importer import Importer
from models.tracks import Track
from .routing import RoutingType
from re import split

class TrackImporter(Importer):
    def __init__(self):
        super().__init__()
        self.source = "tracks"

    def Import(self, file):
        super().Import()

        self.workbook = load_workbook(file, read_only = True)
        #load values from xls
        for sheet in self.workbook:
            try:          
                data = self._ParseSheet(sheet)
            except KeyboardInterrupt:
                self.RemoveDBSession()
                print("KeyboardInterrupt", LogType.error)
                raise KeyboardInterrupt
            except Exception as e:
                self.RemoveDBSession()
                print("Exception reading source data: %s" % str(e), LogType.error)
                return
            #save to database
            self.SaveAllRecordsToDatabase(data)
            data.clear()
        #get location
        self.LoadOSMLocation()

    def _ParseSheet(self, sheet):
        normalize = {'start' : 'start',
                'cíl' : 'finish',
                'od' : 'date_from',
                'do' : 'date_to',
                'vozidlo' : 'vehicle',
                'SPZ' : 'reg_plate',
                'řidič' : 'driver',
                'typ' : 'type',
                'popis' : 'note',
                'tank' : 'tank',
                'Tach. start' : 'tachometer_start',
                'Tach.  cíl' : 'tachometer_finish',
                'vzdálenost metrů' : 'distance',
                'čas' : 'time',
                'stejné' : 'same'}

        data = []
        rows = sheet.rows
        first_row = [cell.value for cell in next(rows)]
        for row in get_tqdm(rows, self.SetState, desc="loading " + sheet.title, total=sheet.max_row):
            record = {}
            for key, cell in zip(first_row, row):
                if cell.data_type == 's':
                    record[normalize.get(key, key)] = cell.value.strip()
                else:
                    record[normalize.get(key, key)] = cell.value
            record['start_address'] = self._ParseAddress(record.get('start'))
            record['finish_address'] = self._ParseAddress(record.get('finish'))
            data.append(Track.as_unique(self.db_session, db_session=self.db_session, data=record))
        return data

    def _ParseAddress(self, address):
        result = split('^(.*),\s?(\d{3}\s\d{2})\s*(.*),\s*(.*)', address)
        if len(result) == 1:
            adresa = address.split(',')
            if len(adresa) < 2:
                raise
            result.insert(1, adresa[0])
            result.insert(2, '')
            result.insert(3, adresa[-2])
            result.insert(4, adresa[-1])

        adresa = result[1].rsplit(' ', 1)
        if len(adresa) > 1 and adresa[1][0].isdigit():
                street, house_number = adresa
        else:
            street = result[1]
            house_number = ''

        return {'street': street, 'house_number' : house_number, 'postal' : result[2].replace(' ', ''), 'city' : result[3], 'country' : result[4]}


    def GetTracks(self, bbox):
        from database import init_db, db_session
        from models.location import Address, OSMLocation
        from sqlalchemy.orm import aliased
        init_db()
        self.db_session = db_session
        self.TestIsRun()
        start_alias = aliased(Address)
        finish_alias = aliased(Address)
        OSMstart_alias = aliased(OSMLocation)
        OSMfinish_alias = aliased(OSMLocation)
        tracks_obj = db_session.query(Track, OSMstart_alias, OSMfinish_alias).join(start_alias, Track.start_address) \
                                        .join(finish_alias, Track.finish_address) \
                                        .join(OSMstart_alias, start_alias.location) \
                                        .join(OSMfinish_alias, finish_alias.location) \
                                        .filter(OSMstart_alias.latitude > bbox.min_latitude, \
                                                OSMstart_alias.latitude < bbox.max_latitude, \
                                                OSMstart_alias.longitude > bbox.min_longitude, \
                                                OSMstart_alias.longitude < bbox.max_longitude) \
                                        .all()
        return tracks_obj






def Run(importFile=None, sourceCity=None):
    importer = TrackImporter()
    try:
        if importer:
            importer.run = True
            importer.Import(importFile)
    except KeyboardInterrupt:
        importer.run = False
        print("KeyboardInterrupt", LogType.info)
    except Exception as e:
        print("Exception reading track source data: %s" % str(e), LogType.error)