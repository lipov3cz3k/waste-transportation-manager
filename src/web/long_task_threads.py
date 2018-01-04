from threading import Thread
from logging import getLogger

from common.utils import LogType, print as trace_print, CheckFolders
from ddr.main import DDRManager
from graph.api import loadGraph
#from graph.main import GraphManager
from graph.bounding_box import BoundingBox

from graph.graph_factory import GraphFactory

logger = getLogger(__name__)

class DDR_thread(Thread):
    def __init__(self):
        self.is_running = False
        self.ddr_manager = DDRManager()
        self.ddr_manager.is_gui = True

        CheckFolders()
        Thread.__init__(self)

    def stop(self):
        self.is_running = False
        self.ddr_manager.run = False

    def run(self):
        self.is_running = True
        self.ddr_manager.run = True
        logger.info("Running from web ...")

        try:
            logger.info("Manage started")
            self.ddr_manager.Manage()
        except KeyboardInterrupt:
            self.ddr_manager.run = False
            logger.warning("KeyboardInterrupt")
        except Exception as e:
            logger.error("Console exception: %s ", str(e))

        logger.info("Manage ended")

        self.is_running = False
        self.ddr_manager.run = False
        logger.info("Web running stopped")

    def status(self):
        if self.ddr_manager:
            return self.ddr_manager.state
        else:
            return {'action':"none", 'percentage':0}

class GRAPH_thread(Thread):
    def __init__(self, bbox=None, graph_pool=[], processCitiesMap=False):
        self.is_running = False
        if not bbox:
            bbox = BoundingBox(16.606296, 49.203635, 16.618806, 49.210056)
        #self.graph_manager = GraphManager(bbox, processCitiesMap)
        self.graph_factory = GraphFactory(442463)
        self.graph_pool = graph_pool

        CheckFolders()
        Thread.__init__(self)

    def stop(self):
        self.is_running = False
        self.graph_factory.run[0] = False

    def run(self):
        self.is_running = True
        self.graph_factory.run[0] = True
        logger.info("Running from web ...")
        graph = self.graph_factory.create()
        if graph:
            graph.save_to_file()
            self.graph_pool.append(graph)

        self.is_running = False
        self.graph_factory.run[0] = False
        self.graph_factory = None
        logger.info("Web running stopped")

    def status(self):
        if self.graph_factory:
            return self.graph_factory.state
        else:
            return {'action':"none", 'percentage':0}

class GRAPH_update_thread(Thread):
    def __init__(self, old_graphID=None, graph_pool=[]):
        self.is_running = False

        # tmp = old_graphID.split("_")
        # bbox = BoundingBox(tmp[1], tmp[2], tmp[3], tmp[4])
        # self.graph_manager = GraphManager(bbox)
        # self.old_graphID = old_graphID
        # self.graph_pool = graph_pool

        # CheckFolders()
        Thread.__init__(self)

    def stop(self):
        pass
        # self.is_running = False
        # self.graph_manager.run[0] = False

    def run(self):
        pass
        # self.is_running = True
        # self.graph_manager.run[0] = True
        # logger.info("Running from web ...")
        # self.graph_manager.graph = loadGraph(self.graph_pool, self.old_graphID)
        # graph, new_msgs_count = self.graph_manager.Update()
        # if graph and new_msgs_count:
        #     if new_msgs_count > 0:
        #         graph.SaveToFile()
        #         self.graph_pool.append(graph)

        # self.is_running = False
        # self.graph_manager.run[0] = False
        # self.graph_manager = None
        # logger.info("Web running stopped")

    def status(self):
        pass
        # if self.graph_manager:
        #     return self.graph_manager.state
        # else:
        #     return {'action':"none", 'percentage':0}
