from logging import getLogger
from models.waste import Container
from models.location import Address, OSMLocation
from tqdm import tqdm
from shapely.geometry import Point, LineString
logger = getLogger(__name__)

def get_db_container_objects(db_session, bounds):
    min_longitude, min_latitude, max_longitude, max_latitude = bounds

    containers_obj = db_session.query(Container).join(Address) \
                                                        .join(Address.location, isouter=True) \
                                                        .filter((Address.latitude > min_latitude) | (OSMLocation.latitude > min_latitude)) \
                                                        .filter((Address.latitude < max_latitude) | (OSMLocation.latitude < max_latitude)) \
                                                        .filter((Address.longitude > min_longitude) | (OSMLocation.longitude > min_longitude)) \
                                                        .filter((Address.longitude < max_longitude) | (OSMLocation.longitude < max_longitude)) \
                                                        .all()
    return containers_obj

def container_location(containers_obj, bounary):
    logger.info("Connecting %d containers to street", len(containers_obj))
    for container in containers_obj:
    #for container in get_tqdm(containers_obj, self.SetState, desc="Connecting containers to streets", total=None):
        #self.TestIsRun()
        location = container.address.location
        if container.address.latitude:
            if location:
                street = container.address.location.road
            else:
                street = container.address.street
            point = Point(container.address.longitude, container.address.latitude)
        elif location:
            street = container.address.location.road
            point = Point(float(location.longitude), float(location.latitude))
        else:
            logger.info("Address %s %s, %s has no OSM equivalent, skipping." % (container.address.street, container.address.house_number, container.address.city))
            continue

        if not bounary.contains(point):
            logger.info("Address %s %s, %s is out of mapping area, skipping." % (container.address.street, container.address.house_number, container.address.city))
            continue

        yield container, (point, street)


def _edge_candidates(graph, point, threshold):
    result = []
    boundary = point.buffer(threshold)
    for (u, v, d) in tqdm(graph.edges(data=True), leave=False):
        if boundary.contains(Point(graph.nodes[u]['lon'], graph.nodes[u]['lat'])) or \
           boundary.contains(Point(graph.nodes[v]['lon'], graph.nodes[v]['lat'])):
           result.append( (u, v) )
    return result

def _geometry(graph, path):
    u = graph.nodes[path[0]]
    v = graph.nodes[path[1]]
    return LineString([(float(u['lon']), float(u['lat'])), (float(v['lon']), float(v['lat']))])

def get_closest_path(graph, street_names, point):
    #bbox = point[0].buffer(0.01, cap_style=3)
    threshold = 0.0005
    path_candidates = street_names.get(point[1], [])
    if not path_candidates or not point[1]:
        logger.warning("Nemam kandidaty pro %s na ulici %s", point[0], point[1])
        #TODO zkus hledat pres vsechny
        path_candidates = _edge_candidates(graph, point[0], threshold)
    #if path_candidates still empty then extend threshold for searching points
    while not path_candidates:
        threshold *= 2
        path_candidates = _edge_candidates(graph, point[0], threshold)
    
    dist = lambda path: point[0].distance(_geometry(graph, path))
    near_way = min(path_candidates, key=dist)    
    return near_way



def get_direction_for_point(a_node, b_node, point, point_id=None):
    """

    """
    direction = None
    try:
        a_point = (float(a_node[1]['lon']), float(a_node[1]['lat']))
        b_point = (float(b_node[1]['lon']), float(b_node[1]['lat']))
        p_to_a = point.distance(Point(a_point))
        p_to_b = point.distance(Point(b_point))
        close,far = (a_point, b_point) if p_to_a < p_to_b else (b_point, a_point)
        p = point.coords[0]

        kriterium = (close[1]-far[1])*(p[0]-close[0])+(far[0]-close[0])*(p[1]-close[1])
        start,end = (a_node[0], b_node[0]) if p_to_a < p_to_b else (b_node[0], a_node[0])
        if kriterium < 0:
            direction = (start, end)
        elif kriterium > 0:
            direction = (end, start)
        else:
            logger.warning("Cannot determine direction")
    except Exception as e:
        logger.error("Direction detection failed")
        raise e
    return direction


def _searchNearby(self, point, ignoreHighway=None):
    from graph.bounding_box import get_bounding_box
    from shapely.geometry import Point as splPoint
    bbox = get_bounding_box(point.y,  point.x, 0.5)

    nodes = (n for n,d in self.G.nodes_iter(data=True) if d['lat'] > bbox.min_latitude and \
                                                            d['lat'] < bbox.max_latitude and \
                                                            d['lon'] > bbox.min_longitude  and \
                                                            d['lon'] < bbox.max_longitude)
    if ignoreHighway:
        nodes = (u for u,v,d in self.G.out_edges(nodes,data=True) if not d['highway'] in ignoreHighway)
    nodes = list(nodes)
    if len(nodes) == 0:
        return None
    try:
        dist = lambda node: point.distance(splPoint(self.G.node[node]['lon'], self.G.node[node]['lat']))
        near_node = min(nodes, key=dist)
        return near_node
    except Exception as e:
        logger.error(str(e))
        raise e


