from argparse import ArgumentParser, FileType
from ddr.main import Run as DDRRun
from graph.main import Run as GraphRun
from graph.bounding_box import BoundingBox
from common.config import local_config
from graph.api import dijkstraPath

if __name__ == '__main__':

    local_config.tqdm_console_disabled = False
    
    parser = ArgumentParser(description='Master\'s Thesis ....')
    parser.add_argument("-d", "--download",
                        action="store_true", dest="download", default=False,
                        help="Download new traffic messages and store them to the DB")
    #Default is Brno - okolo ulice Drobného
    parser.add_argument("-bbox", type=float,
                        nargs=4, dest="bbox", default=[16.606296, 49.203635, 16.618806, 49.210056],
                        help="Defines rectangle around graph. Default: Dobrého, Brno")
    parser.add_argument("-g", "--graph",
                        action="store_true", dest="graph", default=False,
                        help="Create graph and map DDR to the edges. Use -exportCSV for fusion tables export")
    parser.add_argument("-exportCSV",
                        type=FileType('w', encoding='utf-8'), dest="exportCSV",
                        help="If parameter present, program exports graph to CSV file ready to import to Google Fusion tables")
    parser.add_argument("-p", "--path",
                        nargs=3 , dest="path", default=False,
                        help="Compute shortest path between two nodes")

    args = parser.parse_args()

    bbox = BoundingBox(args.bbox[0], args.bbox[1], args.bbox[2], args.bbox[3])

    if(args.download == True):
        DDRRun()
    elif(args.graph == True):
        GraphRun(bbox, args.exportCSV)
    elif(args.path):
        dijkstraPath(str(args.path[0]),str(args.path[1]),str(args.path[2]))
    else:
        parser.print_help()
