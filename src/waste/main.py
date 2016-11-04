from waste.importer import Cheb, Jihlava
from common.utils import LogType, print

def GuessCity(importFile):
    supported_cities = ['cheb', 'jihlava']
    indices = [s for i, s in enumerate(supported_cities) if s in importFile.name.lower()]
    if indices:
        return indices[0]
    else:
        return None

def Run(importFile=None, sourceCity=None):
    importer = None
    if not sourceCity:
        sourceCity = GuessCity(importFile)

    if sourceCity.lower() == 'cheb':
        importer = Cheb()
    elif sourceCity.lower() == 'jihlava':
        importer = Jihlava()
    else:
        pass
    try:
        if importer:
            importer.run = True
            importer.Import(importFile)
    except KeyboardInterrupt:
        importer.run = False
        print("KeyboardInterrupt", LogType.info)