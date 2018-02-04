import logging
import argparse
import sys
from graph.graph_factory import create_save, load
from graph.graph_operations import trackinfo
from importer.import_factory import container_import, streetnet_import
#from waste.main import Run as run_import
from common.config import local_config
from common.utils import CheckFolders as init_data_dirs


def arg_parse():
    parser = argparse.ArgumentParser(description='Waste transportation manager ...')
    parser.add_argument('-v', '--verbose', action='store_true')

    subparsers = parser.add_subparsers(title='actions',
                                       description='actions for WTM',
                                       help='Choose action to be done',
                                       dest='action')

    subparsers.required = True
    # Create
    subparser_create = subparsers.add_parser('create', help='Create new graph')
    source_group = subparser_create.add_mutually_exclusive_group(required=True)
    source_group.add_argument('-r', '--region_id', help='OSM region id (relation)',)
    source_group.add_argument('-b', '--bbox', type=float, nargs=4,
                              metavar=('min_lat', 'min_lon', 'max_lat', 'max_lon'),
                              help='Boundaries of region')

    # Export
    subparser_export = subparsers.add_parser('export', help='Export from existing graph')
    subparser_export.add_argument('graph_name', help='Name of graph, it should be in WTM/graph dir')
    subparser_export.add_argument('--trackinfo')
    subparser_export.add_argument('--citygraph')
    
    #Import
    subparser_import = subparsers.add_parser('import', help='Import various data to database')
    subparser_import.add_argument('--streetnet', type=argparse.FileType('rb'), help='Import StreetNet xsls data')
    subparser_import.add_argument('--containers', type=argparse.FileType('rb'), help='Import containers data')
    subparser_import.add_argument('--city', help='Specify city of importing containers')

    # parser.add_argument("-t", "--tracks",
    #                     action="store_true", dest="processTracks", default=False,
    #                     help="Map tracks from db to the graph and compute shortest path")

    args = parser.parse_args()
    mask = logging.INFO if args.verbose else logging.WARNING
    logging.getLogger().setLevel(mask)
    logging.debug(args)

    return args

def main():
    init_data_dirs()
    logging.basicConfig(
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            logging.FileHandler("{0}/{1}.log".format(local_config.folder_log_files, local_config.log_filename)),
            logging.StreamHandler()
        ])
    args = arg_parse()
    logging.info('Waste Transport Manager started from CLI')

    local_config.tqdm_console_disabled = False

    if args.action == 'create':
        create_save(args.region_id, args.bbox)
    elif args.action == 'export':
        if args.trackinfo:
            trackinfo(args.graph_name, args.trackinfo)
        elif args.citygraph:
            g = load(args.graph_name)
            g.SaveAndShowCitiesMap()
        else:
            load(args.graph_name)
    elif args.action == 'import':
        if args.streetnet:
            streetnet_import(args.streetnet)
        if args.containers:
            container_import(args.containers, args.city)

if __name__ == '__main__':
    main()
