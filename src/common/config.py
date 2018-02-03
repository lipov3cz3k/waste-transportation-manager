from os.path import normpath, join
from os import environ
from platform import system
from common.alertc import TMCUpdateClass


############################ CONFIGURATION ############################
class ftp_config:
    host = 'FTP HOST NAME'
    username = 'FTP USERNAME'
    password = 'FTP PASSWORD'
    data_folder_root = 'data'

class local_config:
    if system() == "Linux":
        root_folder = normpath(join(environ['HOME'], "/www/wtm-data"))
    else:
        root_folder = normpath("D:\\WTM")

    folder_data_root = normpath(join(root_folder, "data"))
    folder_log_files = normpath(join(root_folder, "logs"))
    folder_database = normpath(join(root_folder, "db"))
    db_filename = 'data.db'
    log_filename = 'wtm'
    dump_filename = 'graph.g'
    path_db_file = normpath(join(folder_database, db_filename))
    osmosis_bin = 'S:/_projects/waste-transportation-manager/tools/osmosis/bin/osmosis.bat'
    #osmosis_bin = "D:/_projects/waste-transportation-manager/tools/osmosis/bin/osmosis.bat"
    data_count_per_iteration = 500
    location_count_per_iteration = 500 # TODO: use it
    sleep_between_iteration = 1000 * 1 * 60 * 10 # 10 minutes
    default_last_file_name = "2015-11-14_-1.xml"
    log_file_maxsize = 10000000 # 10mb
    folder_osm_data_root = normpath(join(root_folder, "osm_data"))
    folder_graphs_root = normpath(join(root_folder, "graphs"))
    folder_export_root = normpath(join(root_folder, "export"))
    folder_paths_root = normpath(join(root_folder, "paths"))
    folder_restrictions_root = normpath(join(root_folder, "restrictions"))
    city_map_file = normpath(join(folder_osm_data_root, "jihomoravsky.city" ))
    allowed_tags_node = ['highway','place','name']
    allowed_tags_way = ['oneway', 'highway', 'name', 'ref']
    allowed_place_tags = ['city','town','village', 'hamlet']
    allowed_relation_tags = ['name', 'admin_level']
    allowed_members = ['way', 'node', 'relation']
    allowed_highway_cat = ['motorway','trunk','primary','secondary','tertiary','road','residential','service','motorway_link','trunk_link','primary_link','secondary_link','teriary_link','living_street','unclassified','track']
    excluded_highway_cat = ['track']
    not_allowed_evi = [TMCUpdateClass.parking]
    thread_pool_size_for_mapping = 10
    number_of_stochastic_experiments = 100
    tqdm_console_disabled = True
