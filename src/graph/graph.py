from logging import getLogger
import networkx as nx
from pickle import dump as pickle_dump, load as pickle_load
from os.path import join, isfile, exists
from geojson import Point, Feature, FeatureCollection, LineString
from tqdm import tqdm
import json

from common.service_base import ServiceBase
from .osm.osm_handlers import RouteHandler, CitiesHandler
from common.utils import get_tqdm
from common.config import local_config

logger = getLogger(__name__)

class Graph(ServiceBase):
    def __init__(self, graph_id):
        ServiceBase.__init__(self)
        self.graph_id = graph_id
        self.shape = None
        self.G = nx.DiGraph()
        self.fullG = None
        self.cityGraph = None
        self.containers_connected = False



    def save_to_file(self):
        file_path = join(local_config.folder_graphs_root, '%s.g' % self.get_graph_id())
        meta_file_path = join(local_config.folder_graphs_root, '%s.meta' % self.get_graph_id())
        logger.info("Saving graph %s to file %s", self.graph_id, file_path)
        with open(file_path, 'wb') as output:
            pickle_dump(self.__dict__, output)
        logger.info("Saving graph %s meta", self.graph_id)
        with open(meta_file_path, 'w') as output:
            data = dict(id = self.get_graph_id(),
                        graph_file = '%s.g' % self.get_graph_id(),
                        bounds = self.shape.bounds,
                        shape = Feature(geometry=self.shape, properties={})
                        )
            json.dump(data, output)

    def load_from_file(self, file_path):
        logger.info("Loading graph from %s", file_path)
        with open(file_path, 'rb') as input:
            tmp_dict = pickle_load(input)
            self.__dict__.update(tmp_dict)

    def construct_graph(self, source_pbf, shape):
        from database import init_db, db_session
        init_db()
        logger.info("Constructing graph from %s bounds: %s", source_pbf, shape.bounds)
        self.shape = shape
        rh = RouteHandler()
        rh.apply_file(source_pbf, locations=True)
        rh.split()
        rh.get_graph(self.G)
        logger.info("Reduced graph: %s edges, %s nodes", self.G.number_of_edges(), self.G.number_of_nodes())
        self.fullG = nx.DiGraph()
        rh.get_full_graph(self.fullG)
        logger.info("Full graph: %s edges, %s nodes", self.fullG.number_of_edges(), self.fullG.number_of_nodes())

    def construct_cities_graph(self, source_pbf):
        ch = CitiesHandler()
        ch.apply_file(source_pbf, locations=True)
        ch.connect_regions()

        self.cityGraph = self._supergraph(ch.cities, self.G, self._inCity)
        #self.SaveAndShowCitiesMap(cityGraph)


    def connect_with_containers(self):
        from database import db_session
        from graph.container_tool import get_db_container_objects, container_location, get_closest_path, get_direction_for_point
        from collections import defaultdict
        graph = self.fullG
        if graph is None:
            return

        local_db_session = db_session()
        containers_obj = get_db_container_objects(local_db_session, self.shape.bounds)

        street_names = defaultdict(list)
        for u, v, name in tqdm(graph.edges(data='name'), desc="Preloading street names"):
            street_names[name].append((u, v))

        for container, point in tqdm(container_location(containers_obj, self.shape.minimum_rotated_rectangle), desc="Connecting with containers", total=len(containers_obj)):
            #logger.info("%s at street %s", container, point[1])
            path = get_closest_path(graph, street_names, point)
            if not path:
                continue

            # switch to simplified graph
            id = graph.edges[path]['id']
            
            simple_paths = [(x, y) for x,y,d in self.G.edges(data='id') if d==id]
            if not simple_paths:
                logger.error("Cannot find edge id %s in simplified graph (%s)", id, path)
            simple_path = simple_paths[0]
            a_node = self.G.nodes[simple_path[0]]
            b_node = self.G.nodes[simple_path[1]]
            direction = get_direction_for_point((simple_path[0], a_node), (simple_path[1], b_node), point[0])
            if not direction:
                continue
            if not self.G.has_edge(*direction):
                logger.debug("Edge %s -> %s is not exists, try to reverse", *direction)
                direction = tuple(reversed(direction))
                if not self.G.has_edge(*direction):
                    logger.error("Cannot connect (%s) %s -> %s - even reversed not exists, wtf?", container.id, *direction)
                    continue
            
            self.G.edges[direction[0], direction[1]]['containers'].append(container.id)
            logger.info("(%s) %s -> %s (%s)", container.id, *direction, id)
            

    def connect_with_streetnet(self):
        from database import db_session
        from graph.streetnet_tool import get_db_streetnet_segment_objects, get_closest_path
        from models.cdv import StreetnetOSMRelation
        from shapely.geometry import Point as splPoint
        graph = self.fullG
        if graph is None:
            return

        # pro vsechny useky streetnet najdi nejblizsi osm way
        local_db_session = db_session()
        segment_objs = get_db_streetnet_segment_objects(local_db_session, self.shape.bounds)
        nodes_points = {}
        data = []
        for (n_id, n_d) in tqdm(graph.nodes(data=True), desc="Optimalizing graph for search", leave=False):
            nodes_points[n_id] = splPoint(n_d['lon'], n_d['lat'])
        for segment in tqdm(segment_objs, desc="Paring streetnet with OSM", total=len(segment_objs)):
            path = get_closest_path(graph, nodes_points, splPoint(segment.start_longitude, segment.start_latitude), splPoint(segment.end_longitude, segment.end_latitude))
            if not path:
                logger.error("segment ID %s cannot pair (start node out of range)", segment.id)
                continue
            logger.info("segment ID %s <=> OSM ID %s", segment.id, path['id'])
            data.append(StreetnetOSMRelation(version=1, osm_way_id=path['id'], streetnet=segment))
            if len(data) % 10:
                local_db_session.add_all(data)
                local_db_session.commit()
                data = []

    ################# API #################
    def get_graph_id(self):
        return self.graph_id

    def get_bounding_box(self):
        return self.shape.bounds

    def get_nodes_geojson(self):
        """
        Vrati seznam uzlu silnicni site ve formatu GeoJSON
        """
        features = []
        for n_id, n_d in self.G.nodes(data=True):
            features.append(Feature(id=n_id,
                                    geometry=Point((float(n_d['lon']), float(n_d['lat'])))
                                   ))
        return FeatureCollection(features)

    def get_edges(self):
        return self.G.edges(data=True)

    def get_edge_details(self, n1, n2):
        logger.warning("Not Implemented")

    #####

    def has_city_graph(self):
        return self.cityGraph != None

    #### API: Containers

    def get_edges_with_containers(self):
        logger.warning("Not Implemented")

    #### Api: Import

    def get_path_from_file_geojson(self, path_id):
        import json
        with open(join(local_config.folder_paths_root, '%s.path' % path_id), "r") as myfile:
            paths_pool = {}
            source = json.load(myfile)
            for path in source:
                points = []
                for n in path.get('path'):
                    n = str(n)
                    points.append(((float(self.G.nodes[n]['lon']), float(self.G.nodes[n]['lat']))))
                paths_pool[path.get('id')] = Feature(geometry=LineString(points), style={'color':path.get('color', '#00FF00')})
            fc = FeatureCollection([ v for v in paths_pool.values() ])
            return {'succeded' : True, 'paths' : fc, 'name' : path_id}

# GetContainersGeoJSON
# GetContainerDetails
## GetEdges
## GetEdgeDetails
# LoadPath
# LoadAndFillFrequecy

# ExportSimple
# ExportConainers
# ExportTracksWithPaths
# SaveAndShowCitiesMap
# ExportCityDistanceMatrix

# GetAffectedEdges
# Route

    def _search_by_nuts5(self, nuts5):
        from shapely.geometry import Point as splPoint
        from graph.streetnet_tool import get_closest_node
        p = None
        for n_id, n_d in self.cityGraph.nodes(data=True):
            if nuts5 == n_d.get('nuts5', None):
                p = splPoint(n_d.get('lon'), n_d.get('lat'))
                break
        else:
            return None
        return get_closest_node(self.G, p)

    def route_by_NUTS5(self, start, end):
        if not self.cityGraph:
            return None
        start_node = self._search_by_nuts5(start)
        end_node = self._search_by_nuts5(end)
        try:
            eval, path = nx.bidirectional_dijkstra(self.fullG, start_node, end_node, 'length')
        except nx.NodeNotFound as e:
            logger.error(e.args[0])
        except nx.NetworkXNoPath as e:
            logger.error(e.args[0])
        except nx.NetworkXError as e:
            logger.error(e.args[0])
        return self.route_response(self.fullG, path, eval)

    def route_response(self, g, path, eval):
        points = []
        edges = []
        length = 0
        for n1,n2 in zip(path[0:], path[1:]):
            e = g.edges[(n1,n2)]
            length += e['length']
            edges.append({'id' : e['id'], 'length': e['length'], 'highway' :  e['highway']})
        
        for n in path:
            points.append(((float(g.nodes[n]['lon']), float(g.nodes[n]['lat']))))
        f = Feature(geometry=LineString(points), properties={"length" : length, "eval": eval, "ids" : path, "edges" : edges})
        fc = FeatureCollection([f])    
        return {"succeded" : "true", "paths" : fc}





#########################

    def SaveAndShowCitiesMap(self):
        import matplotlib.pyplot as plt
        if not self.cityGraph:
            logger.info("City graph does not exist.")
            return None

        pos = nx.get_node_attributes(self.cityGraph,'lon')
        pos_lat = nx.get_node_attributes(self.cityGraph,'lat')
        for k, v in pos.items():
            pos[k] = (v, pos_lat[k])

        nx.draw(self.cityGraph, pos=pos)
        node_labels = nx.get_node_attributes(self.cityGraph,'name')
        nx.draw_networkx_labels(self.cityGraph,pos=pos, labels = node_labels)
        edge_labels = nx.get_edge_attributes(self.cityGraph,'length')
        nx.draw_networkx_edge_labels(self.cityGraph, pos=pos,edge_labels=edge_labels)

        plt.show() # display

    def createCityDistanceMatrix(self):
        from functools import partial
        from shapely.geometry import Point as splPoint

        for n1, d1 in get_tqdm(self.cityGraph.nodes(data=True), self.SetState, desc="Computing distance between cities", total=self.cityGraph.number_of_nodes()):
            n1closest = self._searchNearby(splPoint(d1['lon'], d1['lat']),['residential','service','living_street','unclassified'])
            for n2 in self.cityGraph.neighbors(n1):
                d2 = self.cityGraph.node[n2]
                try:
                    n2closest = self._searchNearby(splPoint(d2['lon'], d2['lat']),['residential','service','living_street','unclassified'])

                    if not n1closest:
                        logger.error("Cannot find closest street to admin_centre %s (%s)!!" % (d1['name'],n1))
                        self.cityGraph.edges[(n1,n2)]['length'] = -1
                    elif not n2closest:
                        logger.error("Cannot find closest street to admin_centre %s (%s)!!" % (d2['name'],n2))
                        self.cityGraph.edges[(n1,n2)]['length'] = -1
                    else:
                        route = self._route(n1closest, n2closest)
                        self.cityGraph.edges[(n1,n2)]['length'] = route['paths']['features'][0]['properties']['length']

                except Exception as e:
                    logger.error("Exception cannot compute distance between cities %s (%s) and %s (%s): %s" % (d1['name'],n1,d2['name'],n2,str(e)))
                    self.cityGraph.edges[(n1,n2)]['length'] = -1
        self.ExportCityDistanceMatrix() 

    def _inCity(self,cityShapes,g,a,b,d):
        a_data = {}
        b_data = {}
        n1admin_centre = n2admin_centre = None

        n1 = g.nodes[a].get('city_relation')
        n2 = g.nodes[b].get('city_relation')
        if n1:
            n1city = cityShapes[n1]
            n1admin_centre = n1city['admin_centre']
            a_data['lat'] = float(n1admin_centre.lat)
            a_data['lon'] = float(n1admin_centre.lon)
            a_data['name'] = n1city.get('name')
            a_data['nuts5'] = n1city.get('nuts5')
        else:
            a_data['lat'] = g.nodes[a]['lat']
            a_data['lon'] = g.nodes[a]['lon']
            a_data['name'] = '-'
            a_data['nuts5'] = None
        if n2:
            n2city = cityShapes[n2]
            n2admin_centre = n2city['admin_centre']
            b_data['lat'] = float(n2admin_centre.lat)
            b_data['lon'] = float(n2admin_centre.lon)
            b_data['name'] = n2city.get('name')
            b_data['nuts5'] = n2city.get('nuts5')
        else:
            b_data['lat'] = g.nodes[b]['lat']
            b_data['lon'] = g.nodes[b]['lon'] 
            b_data['name'] = '-'
            b_data['nuts5'] = None

        if n1 == n2 and n1 != None:
            #print(d['id'] + ' is in city ' + n1 + ' -> ignore')
            return None
        elif n1 != n2 and (n1 != None and n2 != None):
            #print(d['id'] + ' is in city ' + n1 + ' and ' + n2 + ' -> leave')
            return (n1admin_centre.id, n2admin_centre.id, d['length'], a_data, b_data)
        elif n1 == None and n2 == None:
            logger.debug("%s is not in any city -> leave", d['id'])
            return (a, b, d['length'], a_data, b_data)
        else:
            if n1 == None:
                logger.debug("%s is partly in city %s -> leave", d['id'], n2)
                return (a, n2admin_centre.id, d['length'], a_data, b_data)
            elif n2 == None:
                logger.debug("%s is partly in city %s -> leave", d['id'], n1)
                return (n1admin_centre.id, b, d['length'], a_data, b_data)
        return None

    def _supergraph(self, cityShapes, g1, keyfunc, allow_selfloops=True):
        from shapely.geometry import Point as splPoint
        g2 = nx.DiGraph()
        #nodelist=list(set(sum([(u,v) for u,v,d in self.G.edges_iter(data=True) if d['highway']=='track'], ())))
        #xx = len(nodelist)
        #yy = self.G.nodes()

        for n, d in get_tqdm(g1.nodes(data=True), self.SetState, desc="Filling city relation", total=g1.number_of_nodes()):
            node = splPoint(float(d['lon']), float(d['lat']))
            for k, city in cityShapes.items():
                if 'polygon' in city and city['polygon'].contains(node):
                    g1.nodes[n].update({'city_relation' : k})
                    break
        for (a,b,d) in get_tqdm(g1.edges(data=True), self.SetState, desc="Creating city graph", total=g1.number_of_edges()):
            # We don't want track category in our supergraph
            if d['highway'] in local_config.excluded_highway_cat:
                continue

            result = keyfunc(cityShapes,g1,a,b,d)
            if result is not None:
                a2,b2,w,a2_data,b2_data = result
                if a2 != b2 or allow_selfloops:
                    g2.add_edge(a2,b2)
                    #try:
                    #    g2[a2][b2]['weight'] += w
                    #except:
                    #    g2[a2][b2]['weight'] = w
                    g2.nodes[a2].update(a2_data)
                    g2.nodes[b2].update(b2_data)
                #for u2,u in [(a2,a),(b2,b)]:
                #    if not u2 in g2:
                #        g2.add_node(u2, original_nodes=set([u]))
                #    else:
                #        try:
                #            g2.node[u2]['original_nodes'].add(u)
                #        except:
                #            g2.node[u2]['original_nodes'] = set([u])
        return g2

    def _searchNearby(self, point, ignoreHighway=None):
        from graph.bounding_box import get_bounding_box
        from shapely.geometry import Point as splPoint
        bbox = get_bounding_box(point.y,  point.x, 0.5)

        nodes = (n for n,d in self.G.nodes(data=True) if d['lat'] > bbox.min_latitude and \
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
            print(str(e), log_type=LogType.error)
            raise e






############## Routing #####################
    def _route(self, startNode, endNode):
        if not startNode or not endNode:
            return {"succeded" : "false", "message" : "Missing start or end point."}
        number_of_experiments = 1
        paths_pool = {}
        for i in range(number_of_experiments):
                
            # Compute path
            try:
                eval, path = nx.bidirectional_dijkstra(self.G, startNode, endNode, 'length')
            except nx.NetworkXNoPath as e:
                return {"succeded" : "false", "message" : str(e.args[0])}
            except nx.NetworkXError as e:
                return {"succeded" : "false", "message" : str(e.args[0])}

            # Save path if not already saved
            h = hash(tuple(path))
            if not h in paths_pool:
                points = []
                edges = []
                length = 0
                for n1,n2 in zip(path[0:], path[1:]):
                    e = self.G.edges[(n1,n2)]
                    length += e['length']
                    edges.append({'id' : e['id'], 'length': e['length'], 'highway' :  e['highway']})

                for n in path:
                    points.append(((float(self.G.nodes[n]['lon']), float(self.G.nodes[n]['lat']))))
                paths_pool[h] = Feature(geometry=LineString(points), properties={"length" : length, "eval": eval, "count" : 1, "ids" : path, "edges" : edges})
            else:
                paths_pool[h].properties['count'] += 1

        # Set path line weight
        for path in paths_pool.values():
            path.properties['weight'] = ((path.properties['count'] * 5) / number_of_experiments) + 5
        fc = FeatureCollection([ v for v in paths_pool.values() ])
        return {"succeded" : "true", "paths" : fc, "number_of_experiments" : number_of_experiments}