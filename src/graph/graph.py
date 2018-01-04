from logging import getLogger
import networkx as nx
from pickle import dump as pickle_dump, load as pickle_load
from os.path import join, isfile, exists
from geojson import Point, Feature, FeatureCollection, LineString

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



    def save_to_file(self, file_path = None):
        if not file_path:
            file_path = join(local_config.folder_graphs_root, '%s.g' % self.get_graph_id())
        logger.info("Saving graph %s to file %s", self.graph_id, file_path)
        with open(file_path, 'wb') as output:
            pickle_dump(self.__dict__, output)

    def load_from_file(self, file_path):
        logger.info("Loading graph from %s", file_path)
        with open(file_path, 'rb') as input:
            tmp_dict = pickle_load(input)
            self.__dict__.update(tmp_dict)

    def construct_graph(self, source_pbf, shape):
        logger.info("Constructing graph from %s bounds: %s", source_pbf, shape.bounds)
        rh = RouteHandler()
        rh.apply_file(source_pbf, locations=True)
        rh.get_graph(self.G)
        self.shape = shape

    def construct_cities_graph(self, source_pbf):
        ch = CitiesHandler()
        ch.apply_file(source_pbf, locations=True)
        ch.connect_regions()

        cityGraph = self._supergraph(ch.cities, self.G, self._inCity)
        #self.SaveAndShowCitiesMap(cityGraph)


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
        logger.warning("Not Implemented")

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


#########################

    def SaveAndShowCitiesMap(self, city_graph):
        import matplotlib.pyplot as plt
        if not city_graph:
            logger.info("City graph does not exist.")
            return None

        pos = nx.get_node_attributes(city_graph,'lon')
        pos_lat = nx.get_node_attributes(city_graph,'lat')
        for k, v in pos.items():
            pos[k] = (v, pos_lat[k])

        nx.draw(city_graph, pos=pos)
        node_labels = nx.get_node_attributes(city_graph,'name')
        nx.draw_networkx_labels(city_graph,pos=pos, labels = node_labels)
        edge_labels = nx.get_edge_attributes(city_graph,'length')
        nx.draw_networkx_edge_labels(city_graph, pos=pos,edge_labels=edge_labels)

        plt.show() # display



    def _inCity(self,cityShapes,g,a,b,d):
        a_data = {}
        b_data = {}

        n1 = self.G.nodes[a].get('city_relation')
        n2 = self.G.nodes[b].get('city_relation')
        if n1:
            n1admin_centre = cityShapes[n1]['admin_centre']
            a_data['lat'] = float(n1admin_centre.lat)
            a_data['lon'] = float(n1admin_centre.lon)
            a_data['name'] = n1admin_centre.tags.get('name')
        else:
            a_data['lat'] = self.G.nodes[a]['lat']
            a_data['lon'] = self.G.nodes[a]['lon']
            a_data['name'] = '-'
        if n2:
            n2admin_centre = cityShapes[n2]['admin_centre']
            b_data['lat'] = float(n2admin_centre.lat)
            b_data['lon'] = float(n2admin_centre.lon)
            b_data['name'] = n2admin_centre.tags.get('name')
        else:
            b_data['lat'] = self.G.nodes[b]['lat']
            b_data['lon'] = self.G.nodes[b]['lon'] 
            b_data['name'] = '-'

        if n1 == n2 and n1 != None:
            #print(d['id'] + ' is in city ' + n1 + ' -> ignore')
            return None
        elif n1 != n2 and (n1 != None and n2 != None):
            #print(d['id'] + ' is in city ' + n1 + ' and ' + n2 + ' -> leave')
            return (n1admin_centre.id, n2admin_centre.id, d['length'], a_data, b_data)
        elif n1 == None and n2 == None:
            logger.debug(d['id'] + ' is not in any city -> leave')
            return (a, b, d['length'], a_data, b_data)
        else:
            if n1 == None:
                logger.debug(d['id'] + ' is partly in city ' + n2 + ' -> leave')
                return (a, n2admin_centre.id, d['length'], a_data, b_data)
            elif n2 == None:
                logger.debug(d['id'] + ' is partly in city ' + n1 + ' -> leave')
                return (n1admin_centre.id, b, d['length'], a_data, b_data)
        return None

    def _supergraph(self, cityShapes, g1, keyfunc, allow_selfloops=True):
        from shapely.geometry import Point as splPoint
        g2 = nx.DiGraph()
        #nodelist=list(set(sum([(u,v) for u,v,d in self.G.edges_iter(data=True) if d['highway']=='track'], ())))
        #xx = len(nodelist)
        #yy = self.G.nodes()

        for n, d in get_tqdm(g1.nodes(data=True), self.SetState, desc="", total=g1.number_of_nodes()):
            node = splPoint(float(d['lon']), float(d['lat']))
            for k, city in cityShapes.items():
                if 'polygon ' in city and city['polygon'].contains(node):
                    g1.nodes[n]['city_relation'] = k
                    break
        for (a,b,d) in get_tqdm(g1.edges(data=True), self.SetState, desc="Creating city graph:", total=g1.number_of_edges()):
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
