from openpyxl import load_workbook
from common.utils import LogType, print, get_tqdm
from waste.importer import Importer
from .routing import RoutingType

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
            except e:
                self.RemoveDBSession()
                print("Exception reading source data: %s" % str(e), LogType.error)
                return
            #save to database
            #self.SaveAllRecordsToDatabase(data)
            data.clear()

    def _ParseSheet(self, sheet):
        normalize = {'start' : 'start',
                'cíl' : 'finish',
                'od' : 'from',
                'do' : 'to',
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
            data.append(record)
        return data


    def PathBasic(self, graphID, start, finish):

        #resolve start/finish from address to node ID

        print(graphID.Route(startNode, endNode))
        





def Run(importFile=None, sourceCity=None):
    importer = TrackImporter()
    try:
        if importer:
            importer.run = True
            importer.Import(importFile)
    except KeyboardInterrupt:
        importer.run = False
        print("KeyboardInterrupt", LogType.info)