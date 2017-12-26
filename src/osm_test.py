from collections import defaultdict

from geopy.distance import vincenty
from tqdm import tqdm
import osmium
import shapely.wkb
import networkx as nx

allowed_highway_cat = ['motorway','trunk','primary','secondary','tertiary','road','residential','service','motorway_link','trunk_link','primary_link','secondary_link','teriary_link','living_street','unclassified','track']
wkbfab = osmium.geom.WKBFactory()

class CounterHandler(osmium.SimpleHandler):
    def __init__(self, bbox):
        osmium.SimpleHandler.__init__(self)
        self.bbox = bbox
        self.num_rel = 0
        self.num_areas = 0
        self.districts = {}
        self.cities = {}

    # def relation(self, r):
    #     if 'boundary' in r.tags and r.tags['boundary'] == 'administrative' and 'admin_level' in r.tags :
    #         if r.tags['admin_level'] == "7": # okres
    #             self.districts[r.id] = dict(name=r.tags['name'],
    #                                        subareas=[member.ref for member in r.members if member.role == "subarea"],
    #                                        cities=[])
    #             print(self.districts[r.id])
    #         elif r.tags['admin_level'] == "8":
    #             try:
    #                 admin_centre = next(member for member in r.members if member.role == "admin_centre")
    #             except StopIteration:
    #                 admin_centre = None
    #             #print("%s %s" % (r.tags.get('name', '-'), admin_centre))
    #             c = self.cities.get(r.id, {})
    #             c["name"] = r.tags.get("name", None)
    #             c["admin_centre"] = admin_centre
    #             c["district"] = None
    #             self.cities[r.id] = c
    #             self.num_rel += 1

    # def area(self, a):
    #     if a.from_way():
    #         return
    #     if 'boundary' in a.tags and a.tags['boundary'] == 'administrative' and 'admin_level' in a.tags :
    #         if a.tags['admin_level'] == "8": # mesto
    #             wkb = wkbfab.create_multipolygon(a)
    #             c = self.cities.get(a.orig_id(), {})
    #             c['polygon'] = shapely.wkb.loads(wkb, hex=True)
    #             self.cities[a.orig_id()] = c
    #             self.num_areas += 1

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

    def _setNodesFromIds(self, nodes_map):
        selected_nodes = [0, len(self.nodes_id)-1]
        self.nodes = []
        for idx, n_id in enumerate(self.nodes_id):
            if idx not in selected_nodes:
                self.nodes.append(None)
            else:
                n = nodes_map.get(n_id)
                self.nodes.append(Node(n_id, n.lat, n.lon))

    def _setDirection(self, nodes_map):
        n0 = nodes_map.get(self.nodes_id[0])
        n1 = nodes_map.get(self.nodes_id[1])
        try:
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

class GraphHandler(osmium.SimpleHandler):
    def __init__(self, bbox):
        osmium.SimpleHandler.__init__(self)
        self.node_histogram = defaultdict(int)
        self.ways = {}
        self.nodes_map = osmium.index.create_map("sparse_mem_map")

    def way(self, w):
        if not 'highway' in w.tags:
            return
        if not w.tags['highway'] in allowed_highway_cat:
            return

        nodes = []
        for n in w.nodes:
            self.nodes_map.set(n.ref, n.location)
            nodes.append(n.ref)
            self.node_histogram[n.ref] += 1
        tags = {}
        for t in w.tags:
            tags[t.k] = t.v 
        self.ways[w.id] = Way(w.id, nodes, tags)

    def splitWaysByIntersectionsRemoveUnusedNodes(self, graph=None, ways=None):
        #use that histogram to split all ways, replacing the member set of ways
        new_ways = {}
        for id, way in tqdm(self.ways.items()):
            split_ways = way.reductive_split(self.node_histogram)
            new_ways[way.id] = []
            # if 'name' in way.tags:
            #     self.streetNames.setdefault(way.tags.get('name'), []).append(way.id)
            for split_way in split_ways:

                first, last = split_way.getFirstLastNodeId()
                distance = 0
                past = self.nodes_map.get(first)
                for current_id in split_way.nodes_id:
                    current = self.nodes_map.get(current_id)
                    distance += vincenty((past.lat, past.lon), (current.lat, current.lon)).meters
                    past = current
                split_way.length = round(distance)
                split_way._setDirection(self.nodes_map)
                if graph is not None:
                    params = dict(id=split_way.id,
                                  length=split_way.length,
                                  highway=split_way.tags['highway'])
                    graph.add_path((first, last), **params)

                    if split_way.tags['highway'] != 'motorway' and ( \
                        ('oneway' not in split_way.tags) or \
                        ('oneway' in split_way.tags and split_way.tags['oneway'] != 'yes' and split_way.tags['oneway'] != '-1')):
                        graph.add_path((last, first), **params)
        
                    node_first = self.nodes_map.get(first)
                    node_last = self.nodes_map.get(last)
                    graph.node[first] = dict(lon=float(node_first.lon), lat=float(node_first.lat), 
                                             #traffic_lights = node_first.tags.get('highway') == 'traffic_signals',
                                             #city_relation = node_first.city_relation
                                             )
                    graph.node[last] = dict(lon=float(node_last.lon), lat=float(node_last.lat), 
                                             #traffic_lights = node_last.tags.get('highway') == 'traffic_signals',
                                             #city_relation = node_last.city_relation
                                             )


                #split_way._setNodesFromIds(self.nodes_map)
                #new_ways[way.id].append(split_way)
        return new_ways







if __name__ == '__main__':
    min_lat, min_lon = 49.109838, 16.463013
    max_lat, max_lon = 49.281244, 16.770630
    
    bl = osmium.osm.Location(min_lon, min_lat)
    tr = osmium.osm.Location(max_lon, max_lat)
    bbox = osmium.osm.Box(bl,tr)

    #x = osmium.index.create_map("sparse_mem_array")

    G = nx.DiGraph()
    ways = {}

    gh = GraphHandler(bbox)
    #gh.apply_file("czech-republic-latest.osm.pbf", locations=True)
    gh.apply_file("albania-latest.osm.pbf", locations=True)
    print(gh.nodes_map.used_memory())
    gh.splitWaysByIntersectionsRemoveUnusedNodes(graph=G)

    h = CounterHandler(bbox)
    h.apply_file("czech-republic-latest.osm.pbf", locations=True)
    #h.apply_file("albania-latest.osm.pbf", locations=True)

    for district in h.districts.values():
        if not district['name'].startswith("okres"):
            continue
        for subarea in district['subareas']:
            city = h.cities.get(subarea, None)
            district['cities'].append(city)
            city['district']=district


    # with open("cities.out", "a") as f:
    #     for city in h.cities.values():
    #         if city['district'] and city['polygon']:
    #             f.write("%s - %s - %s\n" % (city['name'], city['district']['name'], city['polygon']))

    # print("Number of areas: %d relations: %d cities: %d" % (h.num_areas, h.num_rel, len(h.cities)))
