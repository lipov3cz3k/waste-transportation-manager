from waste.main import Run as run_import
from graph.bounding_box import BoundingBox
from graph.main import Run as run_graph
from graph.path_finder import Run as run_path_finder
from common.config import local_config
from ddr.restrictions import LoadFromFile

if __name__ == '__main__':
    local_config.tqdm_console_disabled = False
    #run_import("../data/Cheb/winx_Cheb.20160608.xlsx", "Cheb")
    #run_import("../data/Jihlava/komunal.dbf", "Jihlava")
    run_import("../data/Stavanger/rennedgravde-containere.csv", "Stavanger")
    #bbox = BoundingBox(12.274475,50.023182,12.505188,50.152266)
    #run_graph(bbox)
    #run_path_finder("../data/tracks/vodafone_tracks_23_02_2016.xlsx")
    #run_path_finder("../data/tracks/positrex_v2.xlsx")
    #LoadFromFile("../data/restrictions/Barier_All_pro Vlastika_fin.xlsx")