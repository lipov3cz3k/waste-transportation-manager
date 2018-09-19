from logging import getLogger
from importer.streetnet import StreetNet
from importer.waste import Cheb, Jihlava, Stavanger, Plzen
LOGGER = getLogger(__name__)

def _guessCity(importFile):
    supported_cities = ['cheb', 'jihlava','stavanger','plzen']
    indices = [s for i, s in enumerate(supported_cities) if s in importFile.name.lower()]
    if indices:
        return indices[0]
    else:
        return None

def _run(importer, file):
    try:
        if importer:
            importer.run = True
            importer.Import(file)
    except KeyboardInterrupt:
        importer.run = False
        LOGGER.info("KeyboardInterrupt")

def streetnet_import(importFile=None):
    LOGGER.info("Importing streetnet data from %s", importFile.name)
    _run(StreetNet(), importFile)

def container_import(importFile=None, sourceCity=None):
    LOGGER.info("Importing containers for %s from file %s", sourceCity, importFile.name)
    importer = None
    if not sourceCity:
        sourceCity = _guessCity(importFile)

    if not sourceCity:
        raise Exception('Cannot determine city, try to specify --city param')
    if sourceCity.lower() == 'cheb':
        importer = Cheb()
    elif sourceCity.lower() == 'jihlava':
        importer = Jihlava()
    elif sourceCity.lower() == 'stavanger':
        importer = Stavanger()
    elif sourceCity.lower() == 'plzen':
        importer = Plzen()
    else:
        raise Exception('Unsupported city importer')
    _run(importer, importFile)
