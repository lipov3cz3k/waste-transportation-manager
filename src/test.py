from waste.main import Run as run_import
from graph.bounding_box import BoundingBox
from graph.main import Run as run_graph
from graph.path_finder import Run as run_path_finder
from common.config import local_config

if __name__ == '__main__':
    local_config.tqdm_console_disabled = False
    #run_import("../data/Cheb/winx_Cheb.20160608.xlsx", "Cheb")
    #run_import("../data/jihlava/VUT/komunal.dbf", "Jihlava")
    #bbox = BoundingBox(12.274475,50.023182,12.505188,50.152266)
    #run_graph(bbox)
    run_path_finder("../data/paths/tracks_23_02_2016.xlsx")