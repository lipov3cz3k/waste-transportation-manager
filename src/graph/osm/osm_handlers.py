from logging import getLogger
from collections import defaultdict
from geopy.distance import vincenty
#from tqdm import tqdm
import osmium
import shapely.wkb
from tqdm import tqdm
from common.config import local_config

logger = getLogger(__name__)

class Node:
    def __init__(self, id, lat, lon, tags={}):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.tags = tags
        self.city_relation = None

class Way:
    def __init__(self, id, nodes_id=[], tags={}):
        self.id = id
        self.nodes_id = nodes_id
        self.tags = tags

        self.length = 0
        self.nodes = None
        self.forward = None

    def getFirstLastNodeId(self):
        return (self.nodes_id[0], self.nodes_id[-1])

    def _setDirection(self, nodes_map):
        try:
            n0 = nodes_map.get(self.nodes_id[0])
            n1 = nodes_map.get(self.nodes_id[1])
            self.forward = n0.lat < n1.lat
            self.forward = True if n0.lat == n1.lat and n0.lon < n1.lon else self.forward
        except Exception as e:
            self.forward = True

    def reductive_split(self, dividers):
        def slice_array(ar, dividers):
            result = []
            right = None
            for node in ar[1:-1]:
                if dividers[node] > 1:
                    left = ar[:ar.index(node) + 1]
                    right = ar[ar.index(node):]
                    result += [left]
                    ar = right

            if right:
                result += [right]

            if len(result) == 0:
                result = [ar]

            return result

        slices = slice_array(self.nodes_id, dividers)

        # create a way object for each node-array slice
        ret = []
        i = 0
        for slice in slices:
            new_id = "%s-%d" % (self.id, i)
            new_way = Way(new_id)
            new_way.nodes_id = slice
            new_way.tags = self.tags
            ret.append(new_way)
            i += 1
        return ret

class RouteHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.node_histogram = defaultdict(int)
        self.ways = {}
        self.nodes_map = osmium.index.create_map("sparse_mem_map")
        self.split_ways = []

    def way(self, w):
        if not 'highway' in w.tags:
            return
        if not w.tags['highway'] in local_config.allowed_highway_cat:
            return

        nodes = []
        for n in w.nodes:
            self.nodes_map.set(n.ref, n.location)
            nodes.append(n.ref)
            self.node_histogram[n.ref] += 1
        tags = {}
        for t in w.tags:
            tags[t.k] = t.v 
        self.ways[w.id] = Way(w.id, list(map(int, nodes)), tags)

    def split(self):
        for id, way in tqdm(self.ways.items(), desc="Spliting ways"):
            for split_way in way.reductive_split(self.node_histogram):
                first, _ = split_way.getFirstLastNodeId()
                past = self.nodes_map.get(first)
                distance = 0
                for current_id in split_way.nodes_id:
                    try:
                        current = self.nodes_map.get(current_id)
                        distance += vincenty((past.lat, past.lon), (current.lat, current.lon)).meters
                        past = current
                    except osmium.InvalidLocationError as eee:
                        logger.warning("Distance counter error - skipping node %s (%s)" % (current_id, eee))
                        break
                split_way.length = round(distance)
                split_way._setDirection(self.nodes_map)
                self.split_ways.append(split_way)

    def get_graph(self, graph):
        #use that histogram to split all ways, replacing the member set of ways
        if graph is None:
            return
        for split_way in tqdm(self.split_ways, desc="Generating simplified graph"):
            try:
                first, last = split_way.getFirstLastNodeId()
                node_first = self.nodes_map.get(first)
                node_last = self.nodes_map.get(last)

                params = dict(id=split_way.id,
                            length=split_way.length,
                            highway=split_way.tags['highway'])
                graph.add_path((first, last), **params)
                if split_way.tags['highway'] != 'motorway' and ( \
                    ('oneway' not in split_way.tags) or \
                    ('oneway' in split_way.tags and split_way.tags['oneway'] != 'yes' and split_way.tags['oneway'] != '-1')):
                    graph.add_path((last, first), **params)

                graph.nodes[first].update(dict(lon=float(node_first.lon),
                                                lat=float(node_first.lat), 
                                                #traffic_lights = node_first.tags.get('highway') == 'traffic_signals',
                                                #city_relation = node_first.city_relation
                                            ))

                graph.nodes[last].update(dict(lon=float(node_last.lon),
                                                lat=float(node_last.lat), 
                                                #traffic_lights = node_last.tags.get('highway') == 'traffic_signals',
                                                #city_relation = node_last.city_relation
                                        ))
                                        
            except osmium.InvalidLocationError as eee:
                logger.warning("Way %s has invalid start or end node (%s)" % (split_way.id, eee))

    def get_full_graph(self, graph):
        if graph is None:
            return
        for split_way in tqdm(self.split_ways, desc="Generating full graph"):
            try:
                if len(split_way.nodes_id) <= 1:
                    logger.warning("Way: %s has only one node: %s", split_way.id, split_way.nodes_id)
                    continue
                params = dict(id=split_way.id,
                            length=split_way.length,
                            highway=split_way.tags['highway'],
                            name=split_way.tags.get('name', None))
                graph.add_path(split_way.nodes_id, **params)
                if split_way.tags['highway'] != 'motorway' and ( \
                    ('oneway' not in split_way.tags) or \
                    ('oneway' in split_way.tags and split_way.tags['oneway'] != 'yes' and split_way.tags['oneway'] != '-1')):
                    graph.add_path(reversed(split_way.nodes_id), **params)

                for node_id in split_way.nodes_id:
                    node = self.nodes_map.get(node_id)
                    graph.nodes[node_id].update(dict(lon=float(node.lon),
                                                     lat=float(node.lat)))
            except KeyError as eee:
                logger.warning("Way: %s nodes: %s (KeyError: %s)", split_way.id, split_way.nodes_id, str(eee))    
            except osmium.InvalidLocationError as eee:
                logger.warning("Way %s has invalid start or end node (%s)" % (split_way.id, eee))

class CitiesHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.wkbfab = osmium.geom.WKBFactory()
        self.num_rel = 0
        self.num_areas = 0
        self.districts = {}
        self.cities = {}
        self.places = osmium.index.create_map("sparse_mem_map")


    def node(self, n):
        if 'place' in n.tags and n.tags['place'] in local_config.allowed_place_tags:
            self.places.set(n.id, n.location)

    def relation(self, r):
        if 'boundary' in r.tags and r.tags['boundary'] == 'administrative' and 'admin_level' in r.tags :
            if r.tags['admin_level'] == "7": # okres
                self.districts[r.id] = dict(name=r.tags['name'],
                                           subareas=[member.ref for member in r.members if member.role == "subarea"],
                                           cities=[])
            elif r.tags['admin_level'] == "8":
                try:
                    admin_centre = next(member for member in r.members if member.role == "admin_centre")
                except StopIteration:
                    admin_centre = None
                c = self.cities.get(r.id, {})
                c["name"] = r.tags.get("name", None)
                if admin_centre:
                    c["admin_centre_id"] = admin_centre.ref
                c["district"] = None
                self.cities[r.id] = c
                self.num_rel += 1

    def area(self, a):
        if a.from_way():
            return
        if 'boundary' in a.tags and a.tags['boundary'] == 'administrative' and 'admin_level' in a.tags :
            if a.tags['admin_level'] == "8": # mesto
                wkb = self.wkbfab.create_multipolygon(a)
                c = self.cities.get(a.orig_id(), {})
                c['polygon'] = shapely.wkb.loads(wkb, hex=True)
                self.cities[a.orig_id()] = c
                self.num_areas += 1


    def connect_regions(self):
        for district in self.districts.values():
            if not district['name'].startswith("okres"):
                continue
            for subarea in district['subareas']:
                city = self.cities.get(subarea, None)
                district['cities'].append(city)
                city['district']=district
                if 'admin_centre_id' in city:
                    try:
                        admin_node = self.places.get(city["admin_centre_id"])
                        city["admin_centre"] = Node(city["admin_centre_id"], admin_node.lat, admin_node.lon)
                        city["admin_centre"].city_relation = city
                    except osmium.NotFoundError:
                        logger.info("Admin centre of %s (%s) was not resolved" % (city['name'], city["admin_centre_id"]))
                        city["admin_centre"] = None
                else:
                    logger.info("Admin centre of %s is not defined" % (city['name']))
                    city["admin_centre"] = None
        self.places.clear()