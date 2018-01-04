from logging import getLogger

from time import gmtime, strftime
from common.service_base import ServiceBase
from .map_tool import get_region_pbf
from .graph import Graph

logger = getLogger(__name__)

class GraphFactory(ServiceBase):
    def __init__(self, region):
        ServiceBase.__init__(self)
        self.region = region
        self.graph = None


    def Create(self):
        logger.info('Create')
        # prepare sourece
        region_source_data = get_region_pbf("czech-republic-latest.osm.pbf", self.region)

        # create graph
        graph_id = "%s_%s" % (self.region, strftime("%Y-%m-%d-%H-%M-%S", gmtime()))
        self.graph = Graph()
        self.graph.construct_graph(graph_id, region_source_data[0])
        self.graph.construct_cities_graph(region_source_data[1])

        return self.graph



def Run(bbox=None, exportFile=None, processTracks=None):
    region = 442463
    logger.info('Create region %s', region)

    graph_factory = GraphFactory(region)
    graph_factory.run[0] = True
    graph = graph_factory.Create()
