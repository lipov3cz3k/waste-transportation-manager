import logging
from argparse import ArgumentParser, FileType
from graph.graph_factory import create_save, load
#from waste.main import Run as run_import
from graph.bounding_box import BoundingBox
from common.config import local_config


if __name__ == '__main__':
    logging.basicConfig(
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            logging.FileHandler("{0}/{1}.log".format(local_config.folder_log_files, local_config.log_filename)),
            logging.StreamHandler()
        ],
        level=logging.INFO)
    logging.info('Started')

    local_config.tqdm_console_disabled = False

    parser = ArgumentParser(description='Waste transportation manager ...')
    # parser.add_argument("-i", "--import",
    #                      type=FileType('rb'), dest="import_containers", default=False,
    #                      help="Import container data from various source")
    # parser.add_argument("-c", "--city",
    #                     action="store_true", dest="import_city", default=None,
    #                     help="Specify importing city")

    #Default is Brno - okolo ulice Drobného
    # parser.add_argument("-bbox", type=float,
    #                     nargs=4, dest="bbox", default=[16.606296, 49.203635, 16.618806, 49.210056],
    #                     help="Defines rectangle around graph. Default: Dobrého, Brno")
    # parser.add_argument("-g", "--graph",
    #                     action="store_true", dest="graph", default=False,
    #                     help="Create graph and map DDR to the edges. Use -exportCSV for fusion tables export")
    # parser.add_argument("-exportCSV",
    #                     type=FileType('w', encoding='utf-8'), dest="exportCSV",
    #                     help="If parameter present, program exports graph to CSV file ready to import to Google Fusion tables")
    # parser.add_argument("-t", "--tracks",
    #                     action="store_true", dest="processTracks", default=False,
    #                     help="Map tracks from db to the graph and compute shortest path")

    parser.add_argument("--create", dest="create", type=int)
    # parser.add_argument("-r", "--region", type=int,
    #                     dest="region", default=442314)

    parser.add_argument("--load", dest="load", type=str)
    # parser.add_argument("load")
    # parser.add_argument("-f", "--file", type=str,
    #                     dest="graph_file", default="")



    args = parser.parse_args()

    if args.create:
        create_save(args.create)
    elif(args.load):
        load(args.load)
    else:
        parser.print_help()
    # bbox = BoundingBox(args.bbox[0], args.bbox[1], args.bbox[2], args.bbox[3])


    # if args.import_containers:
    #     pass
    #     #run_import(args.import_containers, args.import_city)
    # elif(args.graph == True):
    #     run_graph(bbox, exportFile = args.exportCSV, processTracks = args.processTracks)
    # else:
    #     parser.print_help()
