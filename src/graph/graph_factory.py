from logging import getLogger
from os.path import join, isfile, exists
from time import gmtime, strftime

from common.service_base import ServiceBase
from common.config import local_config
from .map_tool import get_region_pbf, get_region_shape
from .graph import Graph

logger = getLogger(__name__)

class GraphFactory(ServiceBase):
    def __init__(self):
        ServiceBase.__init__(self)


    def create(self, region):
        logger.info('Create region %s', region)
        # prepare sourece
        region_source_data = get_region_pbf("czech-republic-latest.osm.pbf", region)
 
        shape = get_region_shape(region)
        # create graph
        graph_id = "%s_%s" % (region, strftime("%Y-%m-%d-%H-%M-%S", gmtime()))
        G = Graph(graph_id)
        G.construct_graph(region_source_data[0], shape)
        G.construct_cities_graph(region_source_data[1])
        return G

    def load_from_file(self, graph_id):
        file_path = join(local_config.folder_graphs_root, '%s.g' % graph_id)

        if not exists(file_path):
            raise FileNotFoundError("Cannot find \"%s\"." % (file_path))
        G = Graph(graph_id)
        G.load_from_file(file_path)
        return G



def Run(bbox=None, exportFile=None, processTracks=None):
    region = 442463
    logger.info('Create region %s', region)

    graph_factory = GraphFactory()
    graph_factory.run[0] = True
    #graph = graph_factory.create(region)
    graph = graph_factory.load_from_file("442463_2018-01-04-20-18-50")
    graph.get_nodes_geojson()
