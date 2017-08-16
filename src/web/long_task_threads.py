from threading import Thread

from common.utils import LogType, print as trace_print, CheckFolders
from ddr.main import DDRManager
from graph.api import loadGraph
from graph.main import GraphManager
from graph.bounding_box import BoundingBox


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
        trace_print("Running from web ...", LogType.info)

        try:
            trace_print("Manage started", LogType.info)
            self.ddr_manager.Manage()
        except KeyboardInterrupt:
            self.ddr_manager.run = False
            trace_print("KeyboardInterrupt", LogType.info)
        except Exception as e:
            trace_print("Console exception: %s " % str(e), LogType.error)

        trace_print("Manage ended", LogType.info)

        self.is_running = False
        self.ddr_manager.run = False
        trace_print("Web running stopped", LogType.info)

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
        self.graph_manager = GraphManager(bbox, processCitiesMap)
        self.graph_pool = graph_pool

        CheckFolders()
        Thread.__init__(self)

    def stop(self):
        self.is_running = False
        self.graph_manager.run[0] = False

    def run(self):
        self.is_running = True
        self.graph_manager.run[0] = True
        trace_print("Running from web ...", LogType.info)
        graph = self.graph_manager.Create()
        if graph:
            graph.SaveToFile()
            self.graph_pool.append(graph)

        self.is_running = False
        self.graph_manager.run[0] = False
        self.graph_manager = None
        trace_print("Web running stopped", LogType.info)

    def status(self):
        if self.graph_manager:
            return self.graph_manager.state
        else:
            return {'action':"none", 'percentage':0}

class GRAPH_update_thread(Thread):
    def __init__(self, old_graphID=None, graph_pool=[]):
        self.is_running = False

        tmp = old_graphID.split("_")
        bbox = BoundingBox(tmp[1], tmp[2], tmp[3], tmp[4])
        self.graph_manager = GraphManager(bbox)
        self.old_graphID = old_graphID
        self.graph_pool = graph_pool

        CheckFolders()
        Thread.__init__(self)

    def stop(self):
        self.is_running = False
        self.graph_manager.run[0] = False

    def run(self):
        self.is_running = True
        self.graph_manager.run[0] = True
        trace_print("Running from web ...", LogType.info)
        self.graph_manager.graph = loadGraph(self.graph_pool, self.old_graphID)
        graph, new_msgs_count = self.graph_manager.Update()
        if graph and new_msgs_count:
            if new_msgs_count > 0:
                graph.SaveToFile()
                self.graph_pool.append(graph)

        self.is_running = False
        self.graph_manager.run[0] = False
        self.graph_manager = None
        trace_print("Web running stopped", LogType.info)

    def status(self):
        if self.graph_manager:
            return self.graph_manager.state
        else:
            return {'action':"none", 'percentage':0}
