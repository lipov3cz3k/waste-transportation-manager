from os.path import normpath, join, exists, isfile
from os import unlink
from time import gmtime, strftime
from urllib.request import urlretrieve
from urllib.parse import urlencode
from common.config import local_config
from common.utils import LogType, _print, print, TRACE_FN_CALL, DECORATE_ALL, CheckFolders, progress_hook, removeFile
from .graph_network import Network
from .bounding_box import BoundingBox
from .path_finder import PathFinder

@DECORATE_ALL(TRACE_FN_CALL)
class GraphManager:
    def __init__(self, BBox):
        print("Initialize GraphManager", LogType.trace)
        self.BBox = BBox
        self.state = {}
        self.SetState(action="init", percentage=0)
        self.graph = None

        # highway tag values to use, separated by pipes (|), for instance 'motorway|trunk|primary'
        self.highway_cat = '|'.join(local_config.allowed_highway_cat)
        self.place_cat = '|'.join(local_config.allowed_place_tags)
        self.run = {0: False}
        self.is_gui = False


    def TestIsRun(self):
        if not self.run[0]:
            raise Exception("Service not running")

    def IsBBOXValid(self):
        if not self.BBox:
            print("Missing boundig box", LogType.error)
            raise

        try:
            self.BBox.Validate()
        except Exception as e:
            print("%s" % str(e), LogType.error)
            raise



    def SetState(self, action = None, percentage = None):
        if action != None:
            self.state['action'] = action
        if percentage != None:
            self.state['percentage'] = int(percentage)
        self.state['bbox'] = self.BBox.ToList()

    def Create(self):
        print("Create graph", LogType.info)
        if self.graph:
            print("Graph already exists, returning it", LogType.trace)
            return self.graph

        try:
            self.IsBBOXValid()
        except:
            return None

        osm_data_path = normpath(join(local_config.folder_osm_data_root, "%s.xml" % self.BBox.ToName()))
        # get OSM DATA fike

        try:
            self.GetOSMData(osm_data_path)
            self.TestIsRun()
        except Exception as e:
            print("EXCEPTION: %s" % str(e), log_type=LogType.error)
            removeFile(osm_data_path)
            return None

        # parse xml data to graph structure / object
        print("Parse xml data to graph object", LogType.info)

        graphID = "%s_%s" % (self.BBox.ToName(), strftime("%Y-%m-%d-%H-%M-%S", gmtime()))
        print("New graph id: %s" % (graphID), LogType.trace)
        self.graph = Network(bbox = self.BBox, state=self.state, run=self.run)
        try:
            self.graph.ConstructGraph(graphID, osm_data_path)
        except Exception as e:
            print("Exception in ConstructGraph: %s" % str(e), LogType.error)
            return None


        print("Graph was successfully created.", LogType.info)
        return self.graph


    def Update(self):
        print("Update graph", LogType.info)
        if not self.graph:
            print("Cannot update, old graph doesn't exists", LogType.error)
            return None, None

        try:
            self.IsBBOXValid()
        except:
            return None, None

        self.graph.run = self.run

        old_graphID = self.graph.graphID
        print("Old graph id: %s" % (old_graphID), LogType.trace)

        graphID = "%s_%s" % (self.BBox.ToName(), strftime("%Y-%m-%d-%H-%M-%S", gmtime()))
        print("New graph id: %s" % (graphID), LogType.trace)

        self.graph.state = self.state
        try:
            new_msgs_count = self.graph.UpdateGraph(graphID, old_graphID)
        except Exception as e:
            print("Exception in UpdateGraph: %s" % str(e), LogType.error)
            return None, None

        return self.graph, new_msgs_count

    def DownloadOSMData(self, data_path):
        print("Downloading OSM data", LogType.info)

        try:
            #url = "http://overpass-api.de/api/interpreter"
            #data = {"data" : "area['name'='Jihomoravský kraj']->.boundaryarea;(way['highway'~'%s'](area.boundaryarea););(._;>;);out;" % (self.highway_cat)}
            #url = url+"?"+urlencode(data)
            #print(url)
            #urlretrieve(url, filename=data_path, reporthook=progress_hook(self.state), data=None)
            url = "http://www.overpass-api.de/api/xapi_meta?way[highway=%s][%s]" % (self.highway_cat, self.BBox.ToURL()) # get only ways
            urlretrieve(urlencode(url), filename=data_path, reporthook=progress_hook(self.state), data=None)
        except Exception as e:
            print("Cannot save osm data to file: %s" % str(e), LogType.error)
            removeFile(data_path)
            raise

    def DownloadOSMCities(self, data_path):
        print("Downloading OSM data", LogType.info)
        try:
            #url = "http://overpass-api.de/api/interpreter"
            #data = {"data" : "area['name'='Jihomoravský kraj']->.boundaryarea;(relation['boundary'='administrative']['admin_level'='8'](area.boundaryarea););(._;>;);out;"}
            #url = url+"?"+urlencode(data)
            #print(url)
            #urlretrieve(url, filename=data_path, reporthook=progress_hook(self.state), data=None)
            url = "http://overpass-api.de/api/interpreter?data=(relation['boundary'='administrative']['admin_level'='8'](%s););(._;>;);out;"  % (self.BBox.ToXAPIBBox())
            urlretrieve(urlencode(url), filename=data_path, reporthook=progress_hook(self.state), data=None)
        except Exception as e:
            print("Cannot save osm data to file: %s" % str(e), LogType.error)
            removeFile(data_path)
            raise

    def GetOSMData(self, data_path):
        print("Download OSM data if not exists", LogType.trace)
        if not exists(data_path):
            self.DownloadOSMData(data_path)
        if not exists(data_path+'.city'):
            self.DownloadOSMCities(data_path+'.city')


def Run(bbox=None, exportFile=None, processTracks=None):
    CheckFolders()
    # brno: 16.50,49.11,16.70,49.24
    # palackeho: 16.2953, 50.1147, 16.2979, 50.1170
    # krizovatka u babci: 16.295029, 50.115621, 16.295849, 50.116017
    # vamberk: 16.281610, 50.112488, 16.299977, 50.121624
    # brno - okolo ulice Drobného: 16.606296, 49.203635, 16.618806, 49.210056
    # bratislava: 17.074814,48.103075,17.239265,48.199049
    if not bbox:
        bbox = BoundingBox(16.606296, 49.203635, 16.618806, 49.210056)

    graph_manager = GraphManager(bbox)
    graph_manager.run[0] = True
    graph = graph_manager.Create()
    if graph:
        graph.SaveToFile()
        if exportFile:
            graph.ExportFusionTables(exportFile)
        if processTracks:
            try:
                pathFinder = PathFinder(graph, {})    
                pathFinder.GetTracksWithPaths()
            except KeyboardInterrupt:
                pathFinder.run[0] = False
#            graph.ExportTracksWithPaths()
        print("Nodes <%d>:" % (len(graph.GetNodes())))
        print("Edges <%d>:" % (len(graph.GetEdges())))
        _print("DONE")

if __name__ == '__main__':
    Run()
