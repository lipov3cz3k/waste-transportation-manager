from waste.main import Run as run_import
from graph.bounding_box import BoundingBox
from graph.main import Run as run_graph
if __name__ == '__main__':
    run_import("../data/Cheb/winx_Cheb.20160608.xlsx", "Cheb")
    #run_import("../data/jihlava/VUT/komunal.dbf", "Jihlava")
    bbox = BoundingBox(12.274475,50.023182,12.505188,50.152266)
    #run_graph(bbox)