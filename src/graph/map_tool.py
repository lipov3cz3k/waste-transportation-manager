import subprocess
import re
import sys
from os.path import normpath, join, exists, abspath
from urllib.request import urlretrieve
from shapely.geometry import MultiPolygon, Polygon

from common.config import local_config
from common.utils import removeFile

POLYGONS_URL = "http://polygons.openstreetmap.fr/get_poly.py?id=%s&params=0"

def _execute(cmd):
    print(cmd)
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

def _apply_poly_to_pbf(inputFile, outputFile, polyFile):
    progress_re = re.compile(r"INFO:.*(?P<type>Node|Way) (?P<id>\d+), (?P<ops>\d+.\d+)")
    osmosis_bin = join(abspath(sys.path[0]), local_config.osmosis_bin)

    for line in _execute([osmosis_bin,
                          "--read-pbf-fast", inputFile,
                          "--bounding-polygon", "file=%s"%polyFile, "completeRelations=no", "completeWays=yes",
                          "--tee", "outPipe.0=w", "outPipe.1=r",
                          "--tf", "inPipe.0=w", "accept-ways", "highway=%s" % ','.join(local_config.allowed_highway_cat),
                          "--tf", "reject-relations",
                          "--lp",
                          "--used-node",
                          "--write-pbf", outputFile[0],
                          "--bounding-polygon", "inPipe.0=r", "outPipe.0=r", "file=%s"%polyFile, "completeRelations=yes", "completeWays=no",
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
        _apply_poly_to_pbf(input_file, output_file, poly)

    return output_file

def get_region_shape(region_id):
    poly_file = get_region_poly(region_id)
    return load_region_shape(poly_file)

def load_region_shape(poly_file):
    shape = None
    with open(poly_file, 'r') as f:
            shape = _parse_poly(f)
    return shape

def _parse_poly(lines):
    """ Parse an Osmosis polygon filter file.

        Accept a sequence of lines from a polygon file, return a shapely.geometry.MultiPolygon object.

        http://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format
    """
    in_ring = False
    coords = []

    for (index, line) in enumerate(lines):
        if index == 0:
            # first line is junk.
            continue

        elif in_ring and line.strip() == 'END':
            # we are at the end of a ring, perhaps with more to come.
            in_ring = False

        elif in_ring:
            # we are in a ring and picking up new coordinates.
            ring.append(tuple(map(float, line.split())))

        elif not in_ring and line.strip() == 'END':
            # we are at the end of the whole polygon.
            break

        elif not in_ring and line.startswith('!'):
            # we are at the start of a polygon part hole.
            coords[-1].append([])
            ring = coords[-1][-1]
            in_ring = True

        elif not in_ring:
            # we are at the start of a polygon part.
            coords.append([[]])
            ring = coords[-1][0]
            in_ring = True
    result = []
    for pp in coords:
        for p in pp:
            result.append(Polygon(p))
    return MultiPolygon(result)

if __name__ == '__main__':
    print(get_region_pbf("albania-latest.osm.pbf", 442460))

    #extract_from_poly("D:/WTM/osm_data/albania-latest.osm.pbf", "D:/WTM/osm_data/out2.pbf", "D:/_projects/waste-transportation-manager/shapes/shkoder.poly")