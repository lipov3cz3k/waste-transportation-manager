from waste.importer import Cheb
from graph.bounding_box import BoundingBox
from graph.main import Run as GraphRun

if __name__ == '__main__':
    #ch = Cheb()
    #ch.Import("winx_Cheb.20160608.xlsx")
    bbox = BoundingBox(12.336960,50.046557, 12.435837, 50.103405)
    GraphRun(bbox)