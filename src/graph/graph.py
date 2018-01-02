from common.service_base import ServiceBase
from .osm.osm_handlers import RouteHandler, CitiesHandler
import networkx as nx
from common.utils import get_tqdm
from common.config import local_config

class Graph(ServiceBase):
    def __init__(self):
        ServiceBase.__init__(self)
        self.G = nx.DiGraph()

    def construct_graph(self, graph_id, source_pbf):
        rh = RouteHandler()
        rh.apply_file(source_pbf, locations=True)
        rh.get_graph(self.G)

    def construct_cities_graph(self, source_pbf):
        ch = CitiesHandler()
        ch.apply_file(source_pbf, locations=True)
        ch.connect_regions()

        cityGraph = self.supergraph(ch.cities, self.G, self._inCity)



    def _inCity(self,cityShapes,g,a,b,d):
        a_data = {}
        b_data = {}

        n1 = self.G.node[a]['city_relation']
        n2 = self.G.node[b]['city_relation']
        if n1:
            n1admin_centre = cityShapes[n1]['admin_centre']
            a_data['lat'] = float(n1admin_centre.lat)
            a_data['lon'] = float(n1admin_centre.lon)
            a_data['name'] = n1admin_centre.tags.get('name')
        else:
            a_data['lat'] = self.G.node[a]['lat']
            a_data['lon'] = self.G.node[a]['lon']
            a_data['name'] = '-'
        if n2:
            n2admin_centre = cityShapes[n2]['admin_centre']
            b_data['lat'] = float(n2admin_centre.lat)
            b_data['lon'] = float(n2admin_centre.lon)
            b_data['name'] = n2admin_centre.tags.get('name')
        else:
            b_data['lat'] = self.G.node[b]['lat']
            b_data['lon'] = self.G.node[b]['lon'] 
            b_data['name'] = '-'

        if n1 == n2 and n1 != None:
            #print(d['id'] + ' is in city ' + n1 + ' -> ignore')
            return None
        elif n1 != n2 and (n1 != None and n2 != None):
            #print(d['id'] + ' is in city ' + n1 + ' and ' + n2 + ' -> leave')
            return (n1admin_centre.id, n2admin_centre.id, d['length'], a_data, b_data)
        elif n1 == None and n2 == None:
            print(d['id'] + ' is not in any city -> leave')
            return (a, b, d['length'], a_data, b_data)
        else:
            if n1 == None:
                print(d['id'] + ' is partly in city ' + n2 + ' -> leave')
                return (a, n2admin_centre.id, d['length'], a_data, b_data)
            elif n2 == None:
                print(d['id'] + ' is partly in city ' + n1 + ' -> leave')
                return (n1admin_centre.id, b, d['length'], a_data, b_data)
        return None



    def supergraph(self, cityShapes, g1, keyfunc, allow_selfloops=True):
        from shapely.geometry import Point as splPoint
        g2 = nx.DiGraph()
        #nodelist=list(set(sum([(u,v) for u,v,d in self.G.edges_iter(data=True) if d['highway']=='track'], ())))
        #xx = len(nodelist)
        #yy = self.G.nodes()

        for n, d in get_tqdm(g1.nodes_iter(data=True), self.SetState, desc="", total=g1.number_of_nodes()):
            node = splPoint(float(d['lat']), float(d['lon']))
            for k, city in cityShapes.items():
                if 'polygon ' in city and city['polygon'].contains(node):
                    d['city_relation'] = k
                    break
            g1.node[n] =d
        for (a,b,d) in get_tqdm(g1.edges_iter(data=True), self.SetState, desc="Creating city graph:", total=g1.number_of_edges()):
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
                    g2.node[a2] = a2_data
                    g2.node[b2] = b2_data
                #for u2,u in [(a2,a),(b2,b)]:
                #    if not u2 in g2:
                #        g2.add_node(u2, original_nodes=set([u]))
                #    else:
                #        try:
                #            g2.node[u2]['original_nodes'].add(u)
                #        except:
                #            g2.node[u2]['original_nodes'] = set([u])
        return g2
