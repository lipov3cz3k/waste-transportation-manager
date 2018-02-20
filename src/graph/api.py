from logging import getLogger
from common.config import local_config
from os import listdir
from os.path import exists, splitext, join, getctime
from operator import itemgetter
from graph.map_tool import load_region_shape
from datetime import datetime
import json

logger = getLogger(__name__)

def dijkstraPath(graphID, start, end):
    pass
    # from graph.graph_network import Network
    # graph = Network()
    # graph.LoadFromFile(graphID)
    # print(graph.Route(start,end))

def getGraphList():
    result = []
    suffix = ".meta"
    if not exists(local_config.folder_graphs_root):
        return result
    for file in listdir(local_config.folder_graphs_root):
        if file.endswith(suffix):
            with open(join(local_config.folder_graphs_root, file), 'r') as meta_file:
                data = json.load(meta_file)
                if exists(join(local_config.folder_graphs_root, data.get('graph_file'))):
                    data['timestamp'] = getctime(join(local_config.folder_graphs_root, file))
                    data['datetime'] = datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                    result.append(data)
                else:
                    pass
    result.sort(key=itemgetter('timestamp'), reverse=True)
    return result

def getOSMList():
    result = []
    suffix = ".poly"
    if not exists(local_config.folder_osm_data_root):
        return result
    for file in listdir(local_config.folder_osm_data_root):
        if file.endswith(suffix):
            id = file[:len(suffix)*-1]
            shape = load_region_shape(join(local_config.folder_osm_data_root, file))
            result.append({"id" : id, "bounds" : shape.bounds})
    return result

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

def loadGraph(graph_pool, graph_id=None):
    from graph.graph_factory import GraphFactory
    graph = next((i for i in graph_pool if i.get_graph_id() == graph_id), None)
    if graph:
        return graph
    graph = GraphFactory().load_from_file(graph_id)
    graph_pool.append(graph)
    return graph
