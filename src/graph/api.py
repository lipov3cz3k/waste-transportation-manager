from common.config import local_config
from os import listdir
from os.path import exists, splitext, join
from time import strptime, mktime
import json

def dijkstraPath(graphID, start, end):
    pass
    # from graph.graph_network import Network
    # graph = Network()
    # graph.LoadFromFile(graphID)
    # print(graph.Route(start,end))

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

def loadGraph(graph_pool, graph_id=None):
    from graph.graph_factory import GraphFactory
    graph = next((i for i in graph_pool if i.get_graph_id() == graph_id), None)
    if graph:
        return graph
    graph = GraphFactory().load_from_file(graph_id)
    graph_pool.append(graph)
    return graph

def getImportList(graphID=None, suffix="path"):
    result = []
    if not exists(local_config.folder_paths_root):
        return result
    for file in listdir(local_config.folder_paths_root):
        if graphID and "_".join(graphID.split("_")[0:-1]) not in file:
                continue
        if file.endswith(suffix):
            result.append({"id": splitext(file)[0], "filename" : file})
    return result