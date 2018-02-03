from logging import getLogger
from models.cdv import StreetnetOSMRelation, StreetnetSegments
from tqdm import tqdm
from shapely.geometry import Point
logger = getLogger(__name__)


def get_db_streetnet_segment_objects(db_session, bounds):
    min_latitude, max_latitude, min_longitude, max_longitude = bounds
    segments_obj = db_session.query(StreetnetSegments).filter((StreetnetSegments.start_latitude > min_latitude) | (StreetnetSegments.end_latitude > min_latitude)) \
                                                        .filter((StreetnetSegments.start_latitude < max_latitude) | (StreetnetSegments.end_latitude < max_latitude)) \
                                                        .filter((StreetnetSegments.start_longitude > min_longitude) | (StreetnetSegments.end_longitude > min_longitude)) \
                                                        .filter((StreetnetSegments.start_longitude < max_longitude) | (StreetnetSegments.end_longitude < max_longitude)) \
                                                        .all()
    return segments_obj

def _edge_candidates(graph, point):
    result = []
    boundary = point.buffer(0.0005)
    for (n_id, n_d) in tqdm(graph.items(), leave=False):
        if boundary.contains(n_d):
           result.append( n_id )
    return result


def get_closest_path(graph, nodes_points, start, end):
    node_candidates = _edge_candidates(nodes_points, start)
    if not node_candidates:
        return None
    dist_start = lambda node: start.distance(Point(graph.nodes[node]['lon'], graph.nodes[node]['lat']))
    near_start = min(node_candidates, key=dist_start)

    dist_end = lambda node: end.distance(Point(graph.nodes[node]['lon'], graph.nodes[node]['lat']))
    end_candidates = [n for n in graph[near_start]]
    if not end_candidates:
        return None
    near_end = min(end_candidates, key=dist_end)

    near_edge = graph.edges[(near_start, near_end)]
    return near_edge