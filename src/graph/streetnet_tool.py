from logging import getLogger
from models.cdv import StreetnetOSMRelation, StreetnetSegments
from tqdm import tqdm
from shapely.geometry import Point
logger = getLogger(__name__)


def get_db_streetnet_segment_objects(db_session):

    min_latitude, max_latitude, min_longitude, max_longitude = (50.1, 50.2, 12.7, 12.8)
    segments_obj = db_session.query(StreetnetSegments).limit(100).all()
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
    near_end = min([n for n in graph[near_start]], key=dist_end)

    near_edge = graph.edges[(near_start, near_end)]
    return near_edge