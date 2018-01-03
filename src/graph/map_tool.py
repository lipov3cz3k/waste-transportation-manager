import subprocess
import re
from os.path import normpath, join, exists
from urllib.request import urlretrieve
from shapely.geometry import MultiPolygon, Polygon

from common.config import local_config
from common.utils import removeFile

OSMOSIS_BIN = "S:/_projects/waste-transportation-manager/tools/osmosis/bin/osmosis.bat"
POLYGONS_URL = "http://polygons.openstreetmap.fr/get_poly.py?id=%s&params=0"

def _execute(cmd):
    popen = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stderr.readline, ""):
        yield stdout_line
    popen.stderr.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)

def _download_region_poly(region_id, data_path):
    try:
        urlretrieve(POLYGONS_URL % region_id, filename=data_path,
                    #reporthook=progress_hook(self.state),
                    data=None)
    except Exception as exc:
        print("Cannot get polygon file: %s" % str(exc))
        removeFile(data_path)
        raise

def _extract_from_poly(inputFile, outputFile, polyFile):
    progress_re = re.compile(r"INFO:.*(?P<type>Node|Way) (?P<id>\d+), (?P<ops>\d+.\d+)")

    for line in _execute([OSMOSIS_BIN,
                          "--read-pbf-fast", inputFile,
                          "--bounding-polygon", "file=%s"%polyFile, "completeRelations=yes", "completeWays=yes",
                          "--tee", "outPipe.0=w", "outPipe.1=r",
                          "--tf", "inPipe.0=w", "accept-ways", "highway=%s" % ','.join(local_config.allowed_highway_cat),
                          "--tf", "reject-relations",
                          "--lp",
                          "--used-node",
                          "--write-pbf", outputFile[0],
                          "--tf", "inPipe.0=r", "outPipe.0=r", "accept-relations", "admin_level=7,8",
                           "--used-way", "inPipe.0=r", "outPipe.0=r",
                           "--used-node", "inPipe.0=r", "outPipe.0=r",
                           "--lp", "inPipe.0=r", "outPipe.0=r",
                          "--write-pbf", "inPipe.0=r", outputFile[1]
                          ]):
        match = progress_re.match(line)
        if match:
            print("typ %s id %s ops %s" % (match.group("type"), match.group("id"), match.group("ops")))

def get_region_poly(region_id):
    poly = normpath(join(local_config.folder_osm_data_root, "%s.poly" % region_id))
    if not exists(poly):
        _download_region_poly(region_id, poly)
    return poly

def get_region_pbf(input_file_name, region_id):
    output_file = (normpath(join(local_config.folder_osm_data_root, "%s.ways.pbf" % region_id)), 
                   normpath(join(local_config.folder_osm_data_root, "%s.city.pbf" % region_id)))
    if not exists(output_file[0]) or not exists(output_file[1]):
        poly = get_region_poly(region_id)
        input_file = normpath(join(local_config.folder_osm_data_root, input_file_name))
        if not exists(input_file):
            raise Exception("Missing source PBF file")
        _extract_from_poly(input_file, output_file, poly)

    return output_file

def parse_poly(lines):
    """ Parse an Osmosis polygon filter file.

        Accept a sequence of lines from a polygon file, return a shapely.geometry.MultiPolygon object.

        http://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format
    """
    in_ring = False
    coords = []
    
    for (index, line) in enumerate(lines):
        if index <= 1:
            # first line is junk.
            continue
        
        elif index == 2:
            # second line is the first polygon ring.
            coords.append([[], []])
            ring = coords[-1][0]
            in_ring = True
        
        elif in_ring and line.strip() == 'END':
            # we are at the end of a ring, perhaps with more to come.
            in_ring = False
    
        elif in_ring:
            # we are in a ring and picking up new coordinates.
            ring.append(map(float, line.split()))
    
        elif not in_ring and line.strip() == 'END':
            # we are at the end of the whole polygon.
            break
    
        elif not in_ring and line.startswith('!'):
            # we are at the start of a polygon part hole.
            coords[-1][1].append([])
            ring = coords[-1][1][-1]
            in_ring = True
    
        elif not in_ring:
            # we are at the start of a polygon part.
            coords.append([[], []])
            ring = coords[-1][0]
            in_ring = True
    
    return MultiPolygon(coords)

if __name__ == '__main__':
    print(get_region_pbf("albania-latest.osm.pbf", 442460))

    #extract_from_poly("D:/WTM/osm_data/albania-latest.osm.pbf", "D:/WTM/osm_data/out2.pbf", "D:/_projects/waste-transportation-manager/shapes/shkoder.poly")