from common.config import local_config
from os import listdir
from os.path import exists
from time import strptime, mktime

def dijkstraPath(graphID, start, end):
    from graph.graph_network import Network
    graph = Network()
    graph.LoadFromFile(graphID)
    print(graph.DijkstraPath(start,end))

def getGraphList():
    result = []
    suffix = ".g"
    if not exists(local_config.folder_graphs_root):
        return result
    for file in listdir(local_config.folder_graphs_root):
        if file.endswith(suffix):
            id = file[:len(suffix)*-1]
            time = id.split("_")[-1]
            coords = id.split("_")[1:-1]
            result.append({"id": id, "coords" : coords, "timestamp" : time})
    result.sort(key=lambda x: mktime(strptime(x['timestamp'],"%Y-%m-%d-%H-%M-%S")), reverse=True)
    return result

def getOSMList():
    result = []
    suffix = ".xml"
    if not exists(local_config.folder_osm_data_root):
        return result
    for file in listdir(local_config.folder_osm_data_root):
        if file.endswith(suffix):
            id = file[:len(suffix)*-1]
            coords = id.split("_")[1:]
            result.append({"id" : id, "coords" : coords})
    return result

def loadGraph(graph_pool, graphID=None):
    from graph.graph_network import Network
    graph = next((i for i in graph_pool if i.GetGraphID() == graphID), None)
    if graph:
        return graph
    graph = Network()
    graph.LoadFromFile(graphID)
    graph_pool.append(graph)
    return graph