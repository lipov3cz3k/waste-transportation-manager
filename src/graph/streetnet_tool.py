from logging import getLogger
from models.cdv import StreetnetOSMRelation, StreetnetSegments
from tqdm import tqdm
from shapely.geometry import Point
logger = getLogger(__name__)


def get_db_streetnet_segment_objects(db_session, bounds):
    min_longitude, max_longitude, min_latitude, max_latitude = bounds
    segments_obj = db_session.query(StreetnetSegments).filter((StreetnetSegments.start_latitude > min_latitude) | (StreetnetSegments.end_latitude > min_latitude)) \
                                                        .filter((StreetnetSegments.start_latitude < max_latitude) | (StreetnetSegments.end_latitude < max_latitude)) \
                                                        .filter((StreetnetSegments.start_longitude > min_longitude) | (StreetnetSegments.end_longitude > min_longitude)) \
                                                        .filter((StreetnetSegments.start_longitude < max_longitude) | (StreetnetSegments.end_longitude < max_longitude)) \
                                                        .all()
    return segments_obj

def _node_candidates(graph, point):
    result = []
    max_iter = 10
    i = 1
    presnost = 0.0005
    while not result or i == max_iter:
        boundary = point.buffer(presnost)
        for (n_id, n_d) in tqdm(graph.items(), leave=False):
            if boundary.contains(n_d):
                result.append( n_id )
        i +=1
        presnost *= 10
    return result


def get_closest_path(graph, nodes_points, start, end):
    node_candidates = _node_candidates(nodes_points, start)
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

def get_closest_node(graph, point, ignoreHighway=None):
    nodes_points = {}
    for (n_id, n_d) in tqdm(graph.nodes(data=True), desc="Optimalizing graph for search", leave=False):
            nodes_points[n_id] = Point(n_d['lon'], n_d['lat'])
    node_candidates = _node_candidates(nodes_points, point)
    if ignoreHighway:
            nodes = (u for u,v,d in graph.out_edges(node_candidates,data=True) if not d['highway'] in ignoreHighway)
            node_candidates = list(nodes)

    logger.debug("Node candidates for %s: %s", point, node_candidates)
    dist = lambda node: point.distance(Point(graph.nodes[node]['lon'], graph.nodes[node]['lat']))
    return min(node_candidates, key=dist)