from pickle import dump as pickle_dump, load as pickle_load
import networkx as nx
import numpy as np
import csv
from random import random
from os.path import join, isfile, exists
from os import unlink
from geojson import Point, Feature, FeatureCollection, LineString
from datetime import datetime
from common.config import local_config
from common.alertc import TMCUpdateClass
from common.utils import LogType, _print, print, TRACE_FN_CALL, DECORATE_ALL, get_tqdm, Season, SeasonCoefficient, DayTime, DayTimeCoefficient, removeFile
from .osm.osm_parser import OSMParser
from .routing import RoutingType, GetPenaltyMul
from .statistics import createCorrelation, correlationVisualize

import matplotlib.pyplot as plt

@DECORATE_ALL(TRACE_FN_CALL)
class Network:
    def __init__(self, bbox = None, state = None, run = {0: False}):
        self.state = state
        self.graphID = None
        self.bbox = bbox
        self.max_penalty = 0
        self.G = nx.DiGraph()
        self.cityGraph = None
        self.Cities = nx.DiGraph()
        self.season_correlation = None
        self.daytime_correlation = None
        self.total_incidents = 0
        self.run = run

    def TestIsRun(self):
        if not self.run[0]:
            raise Exception("Service not running")

    def ConstructGraph(self, graphID, osm_path_xml_data):
        from database import init_db, db_session
        init_db()
        self.graphID = graphID

        try:
            osm = OSMParser(self.graphID, bbox=self.bbox, state=self.state, run=self.run)
            osm.ParseFromXMLFile(osm_path_xml_data)
#            osm.ConnectDDRDataWithWays(db_session)
#            osm.ConnectContainersWithWays(db_session)
            self.SetState(action="Saving parsed osm to file", percentage=0)
            osm.SaveToFile()
            self.SetState(action="Saving parsed osm to file", percentage=100)
        except Exception as e:
            print("Exception in creating/parsing/connecting OSM: %s" % str(e), log_type=LogType.error)
            db_session.remove()
            removeFile(join(local_config.folder_graphs_root, '%s.o' % self.graphID))
            raise Exception("Cannot parse/connect OSM")

        try:
            self.SetState(action="Add edges to graph, compute evaluation", percentage=0)
            cityShapes = osm.GetLAU2Shapes()
            self.fillGraphWithData(osm, db_session, cityShapes)
            self.createCityDistanceMatrix(cityShapes)



            self.SetState(action="Add edges to graph, compute evaluation", percentage=100)
            self.SetState(action="Create correlation", percentage=0)
            self.season_correlation = createCorrelation(self.G, 'season')
            self.daytime_correlation = createCorrelation(self.G, 'daytime')
            self.SetState(action="Create correlation", percentage=100)
        except Exception as e:
            print("Exception in filling graph with data: %s" % str(e), log_type=LogType.error)
            db_session.remove()
            removeFile(join(local_config.folder_graphs_root, '%s.o' % self.graphID))
            raise Exception("Cannot fill graph")

        db_session.remove()

    def UpdateGraph(self, graphID, old_graphID):
        from ddr.database import init_db, db_session
        init_db()
        self.graphID = graphID

        try:
            osm = OSMParser(self.graphID, state=self.state, run=self.run)
            osm.LoadFromFile(old_graphID)
            new_msgs_count = osm.ConnectDDRDataWithWays(db_session)
            if new_msgs_count > 0:
                self.SetState(action="Saving parsed osm to file", percentage=0)
                osm.SaveToFile()
                self.SetState(action="Saving parsed osm to file", percentage=100)
        except Exception as e:
            print("Exception in loading/connecting OSM: %s" % str(e))
            db_session.remove()
            removeFile(join(local_config.folder_graphs_root, '%s.o' % self.graphID))
            raise Exception("Cannot load/connect OSM")

        try:
            if new_msgs_count > 0:
                self.fillGraphWithData(osm, db_session)
                self.season_correlation = createCorrelation(self.G, 'season')
                self.daytime_correlation = createCorrelation(self.G, 'daytime')
        except Exception as e:
            print("Exception in filling graph with data: %s" % str(e), log_type=LogType.error)
            db_session.remove()
            removeFile(join(local_config.folder_graphs_root, '%s.o' % self.graphID))
            raise Exception("Cannot fill graph")

        db_session.remove()
        return new_msgs_count

    def fillGraphWithData(self, osm, db_session, cityShapes = None):
        from shapely.geometry import Point as splPoint
        for id, uniq_w in get_tqdm(osm.ways.items(), self.SetState, desc="Add edges to graph, compute evaluation", total=None):
            for w in uniq_w:
                if not 'highway' in w.tags:
                    continue
                self.TestIsRun()
                incidents = []# w.GetIncidents(db_session)
                self.total_incidents += len(incidents)
                penalty_multiplicator = GetPenaltyMul(incidents)
                if penalty_multiplicator > self.max_penalty:
                    self.max_penalty = penalty_multiplicator
                containers = w.GetContainers(db_session, False)
                params = {'id':w.id, 'length':w.length, 'evaluation':w.length, 'highway':w.tags['highway'], 'msgs':w.msgs, 'incidents':incidents, 'ref':w.tags.get('ref'), 'penalty_multiplicator':penalty_multiplicator, 'containers' : containers}
                node_first, node_last = w.GetFirstLastNodeId()
                self.G.add_path((node_first.id, node_last.id), **params)

                if ('oneway' not in w.tags and w.tags['highway'] != 'motorway') or ('oneway' in w.tags and w.tags['oneway'] != 'yes' and w.tags['oneway'] != '-1' and w.tags['highway'] != 'motorway'):
                    containers =  w.GetContainers(db_session, True)
                    params['containers'] = containers
                    self.G.add_path((node_last.id, node_first.id), **params)

                n1 = splPoint(float(node_first.lat), float(node_first.lon))
                n2 = splPoint(float(node_last.lat), float(node_last.lon))
                for k, city in cityShapes.items():
                    if city['shape'].contains(n1):
                        node_first.city_relation = k
                    if city['shape'].contains(n2):
                        node_last.city_relation = k
                    if node_first.city_relation and node_last.city_relation:
                        break

                self.G.node[node_first.id] = dict(lon=float(node_first.lon), lat=float(node_first.lat), traffic_lights=node_first.tags.get('highway') == 'traffic_signals', city_relation = node_first.city_relation)
                self.G.node[node_last.id] = dict(lon=float(node_last.lon), lat=float(node_last.lat), traffic_lights=node_last.tags.get('highway') == 'traffic_signals', city_relation = node_last.city_relation)

            osm.ways[id] = None
          

    def createCityDistanceMatrix(self, cityShapes):
        from functools import partial
        from shapely.geometry import Point as splPoint
        self.cityGraph = self.supergraph(cityShapes, self.G, self._inCity)
        

        for n1, d1 in self.cityGraph.nodes_iter(data=True):
            n1closest = self._searchNearby(splPoint(d1['lon'], d1['lat']))
            for n2 in nx.all_neighbors(self.cityGraph, n1):
                d2 = self.cityGraph.node[n2]
                try:
                    n2closest = self._searchNearby(splPoint(d2['lon'], d2['lat']))

                    if n1closest and n2closest:
                        eval, path = nx.bidirectional_dijkstra(self.G, n1closest, n2closest, 'evaluation')
                        self.cityGraph.edge[n1][n2]['length'] = eval
                    else:
                        print("Cannot find closest street to admin_centre %s (%s) or %s (%s)!!" % (d1['name'],n1,d2['name'],n2), log_type=LogType.error)
                        self.cityGraph.edge[n1][n2]['length'] = -1
                except Exception as e:
                    print("Exception cannot compute distance between cities %s (%s) and %s (%s): %s" % (d1['name'],n1,d2['name'],n2,str(e)), log_type=LogType.error)
                    self.cityGraph.edge[n1][n2]['length'] = -1


        # Save as image

        pos = nx.get_node_attributes(self.cityGraph,'lon')
        pos_lat = nx.get_node_attributes(self.cityGraph,'lat')
        for k, v in pos.items():
            pos[k] = (v, pos_lat[k])

        nx.draw(self.cityGraph, pos=pos)
        node_labels = nx.get_node_attributes(self.cityGraph,'name')
        nx.draw_networkx_labels(self.cityGraph,pos=pos, labels = node_labels)
        edge_labels = nx.get_edge_attributes(self.cityGraph,'length')
        nx.draw_networkx_edge_labels(self.cityGraph, pos=pos,edge_labels=edge_labels)

        plt.savefig(join(local_config.folder_export_root, '%s.svg' % self.graphID), format="svg")
        plt.show() # display
      

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
        g2 = nx.DiGraph()
        
        for (a,b,d) in g1.edges_iter(data=True):
            result = keyfunc(cityShapes,g1,a,b,d)
            if result is not None:
                a2,b2,w,a2_data,b2_data = result
                if a2 != b2 or allow_selfloops:
                    g2.add_edge(a2,b2)
                    try:
                        g2[a2][b2]['weight'] += w
                    except:
                        g2[a2][b2]['weight'] = w
                    g2.node[a2] = a2_data
                    g2.node[b2] = b2_data
                for u2,u in [(a2,a),(b2,b)]:
                    if not u2 in g2:
                        g2.add_node(u2, original_nodes=set([u]))
                    else:
                        try:
                            g2.node[u2]['original_nodes'].add(u)
                        except:
                            g2.node[u2]['original_nodes'] = set([u])
        return g2



    def createCityGraph(self, osm):
        for id, uniq_city in get_tqdm(osm.city_nodes.items(), self.SetState, desc="Add cities to graph, compute evaluation", total=None):
            self.TestIsRun()
            params = {'lon':float(uniq_city.lon), 'lat':float(uniq_city.lat), 'name' : uniq_city.tags['name']}
            self.Cities.add_node(id, **params)
        return False


    def SaveToFile(self, file_path = None):
        if not file_path:
            file_path = join(local_config.folder_graphs_root, '%s.g' % self.GetGraphID())
        with open(file_path, 'wb') as output:
            pickle_dump(self.__dict__, output)

    def LoadFromFile(self, graphID):
        file_path = join(local_config.folder_graphs_root, '%s.g' % graphID)

        if not exists(file_path):
            raise FileNotFoundError("Cannot find \"%s\". Run GRAPH first" % (file_path))
        with open(file_path, 'rb') as input:
            tmp_dict = pickle_load(input)
            self.__dict__.update(tmp_dict)


    def GetGraphID(self):
        return self.graphID

    def SetState(self, action = None, percentage = None):
        if action != None:
            self.state['action'] = action
        if percentage != None:
            self.state['percentage'] = int(percentage)

    def GetNodes(self):
        return self.G.nodes()

    def GetEdges(self):
        return self.G.edges(data=True)

    def GetNodesGeoJSON(self):
        features = []
        for n_id in self.G.nodes_iter():
            features.append( Feature(id=n_id, geometry=Point((float(self.G.node[n_id]['lon']), float(self.G.node[n_id]['lat'])))) )
        return FeatureCollection(features)

    def GetContainersGeoJSON(self, n1=None, n2=None):
        from graph.bounding_box import BoundingBox

        result = {};
        if n1 and n2:
            e = self.G[n1][n2]
            containers = e.get('containers')
            for container in containers:
                result.setdefault(container.get('waste_code'),[]).append(Feature(id=container.get('id'), geometry=Point((float(container.get('lon')), float(container.get('lat')))), properties=container))
            # oposit direction
            if n1 in self.G[n2]:
                e = self.G[n2][n1]
                containers = e.get('containers')
                for container in containers:
                    result.setdefault(container.get('waste_code'),[]).append(Feature(id=container.get('id'), geometry=Point((float(container.get('lon')), float(container.get('lat')))), properties=container))
        else:
            for n1, n2, e in self.G.edges_iter(data=True):
                containers = e.get('containers')
                for container in containers:
                    result.setdefault(container.get('waste_code'),[]).append(Feature(id=container.get('id'), geometry=Point((float(container.get('lon')), float(container.get('lat')))), properties=container))
        for key, value in result.items():
            result[key] = FeatureCollection(value)  
        return result

    def GetContainerDetails(self, id):
        from database import db_session
        from models.waste import Container

        containers_details = []
        containers = db_session.query(Container).filter(Container.id == id).all()
        for container in containers:
            containers_details.append({ 'id' : container.id, 
                                        'container_type' : container.container_type,
                                        'waste_type' : container.waste_type,
                                        'waste_name' : container.waste_name,
                                        'interval' : container.interval,
                                        'days' : container.days_orig,
                                        'city' : container.address.city,
                                        'street' : container.address.street,
                                        'house_number' : container.address.house_number
                                        })

        db_session.remove()
        return {'containers' : containers_details}

    def GetEdgesWithContainers(self):
        edges = []
        for n1, n2, e in self.G.edges_iter(data=True):
            containers = e.get('containers')
            if len(containers) >= 1:
                start = (float(self.G.node[n1]['lon']), float(self.G.node[n1]['lat']))
                end = (float(self.G.node[n2]['lon']), float(self.G.node[n2]['lat']))
                f = Feature(geometry=LineString([start, end]), properties={'n1' : n1, 'n2' : n2})
                edges.append(f)
        return FeatureCollection(edges)

    def GetAffectedEdges(self):
        edges = []
        denominator = (self.max_penalty - 1)
        for n1, n2, e in self.G.edges_iter(data=True):
            if len(e['incidents']) > 0:
                start = (float(self.G.node[n1]['lon']), float(self.G.node[n1]['lat']))
                end = (float(self.G.node[n2]['lon']), float(self.G.node[n2]['lat']))
                opacity = (((e['penalty_multiplicator']  - 1) * (0.7)) / denominator) + 0.3 # newMin = 0.3

                f = Feature(geometry=LineString([start, end]), properties={'n1' : n1, 'n2' : n2, 'opacity' : opacity})
                edges.append(f)
        return FeatureCollection(edges)

    def GetEdgeDetails(self, n1, n2):
        from database import db_session
        edge = self.G[n1][n2]
        msgs = []
        for m in edge['msgs']:
            m = db_session.merge(m)
            msgs.append({'m_id' : m.id, 'txt' : m.MTXT.value})
        db_session.remove()

        details = {'id' : edge['id'], 'length': edge['length'], 'multiplicator' : edge['penalty_multiplicator'], 'msgs' : msgs}
        return details

############# Export functions ################
    def ExportSimple(self):
        
        file_path = join(local_config.folder_export_root, '%s' % self.graphID)

        #return nx.adjacency_matrix(self.G, weight='length')
        matrix = nx.to_numpy_matrix(self.G, weight='length')
        np.savetxt(file_path+"_d.csv", matrix, fmt="%i", delimiter=",")
        
        with open(file_path+"_n.csv", 'w',newline="\n", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['node','lat', 'lon','traffic_lights'])
            for n, d in self.G.nodes_iter(data=True):
                writer.writerow([n, d.get('lat'), d.get('lon'), 'T' if d.get('traffic_lights') else 'F'])
        return self.G.nodes(data=True)

    def ExportConainers(self):
        from database import db_session
        from models.waste import Container
        file_path = join(local_config.folder_export_root, '%s' % self.graphID)

        waste_codes_obj = db_session.query(Container.waste_code).group_by(Container.waste_code).all()
        for waste_code in waste_codes_obj:
            with open(file_path+"_containers_"+str(waste_code[0])+".csv", 'w',newline="\n", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(['edge','n1', 'n2','length','highway','contaniners'])
                for n1, n2, e in self.G.edges(data=True):
                    containers = [d for d in e['containers'] if d.get('waste_code') == waste_code[0]]
                    if not containers:
                        continue
                    writer.writerow([e['id'], n1, n2, e['length'], e['highway'], containers])
        return self.G.nodes(data=True)

    def ExportTracksWithPaths(self):
        file_path = join(local_config.folder_export_root, '%s' % self.graphID)
        result = self.GetTracksWithPaths()
        with open(file_path+"_tracks.txt", 'w',newline="\n", encoding="utf-8") as f:
            _print(result, file=f)
            f.flush()

############# Import functions ################

    def LoadPath(self, pathID):
        import json
        with open(join(local_config.folder_paths_root, '%s.path' % pathID), "r") as myfile:
            paths_pool = {}
            source = json.load(myfile)
            for path in source:
                points = []
                for n in path.get('path'):
                    n = str(n)
                    points.append(((float(self.G.node[n]['lon']), float(self.G.node[n]['lat']))))
                paths_pool[path.get('id')] = Feature(geometry=LineString(points), style={'color':path.get('color', '#00FF00')})
            fc = FeatureCollection([ v for v in paths_pool.values() ])
            return {'succeded' : True, 'paths' : fc, 'name' : pathID}

    def LoadAndFillFrequecy(self, fileName):
        import csv
        with open(join(local_config.folder_paths_root, '%s.freq' % fileName), "r") as csvinput:
            with open(join(local_config.folder_paths_root, '%s.out.freq' % fileName), 'w', newline="\n", encoding="utf-8") as csvoutput:
                writer = csv.writer(csvoutput, delimiter='\t')
                for row in csv.reader(csvinput,delimiter='\t'):
                    if self.G.has_edge(row[0],row[1]):
                        e = self.G.edge[row[0]][row[1]]
                        writer.writerow(row+[e.get('id'), e.get('ref')])
                    else:
                        writer.writerow(row+['no_edge'])
        return {'succeded' : True}

############# Tracks management ################
    def GetTracksWithPaths(self, safeToDb = True):
        from .path_finder import TrackImporter
        from shapely.geometry import Point as splPoint
        from database import db_session
        from models.path import Path
        importer = TrackImporter()
        tracks_obj = []
        try:
            if importer:
                importer.run = True
                tracks_obj = importer.GetTracks(self.bbox)
        except KeyboardInterrupt:
            importer.run = False
            print("KeyboardInterrupt", LogType.info)
        except Exception as e:
            print("Exception reading source data: %s" % str(e), LogType.error)
            return
        result = []
        db_temp = []
        for track in get_tqdm(tracks_obj, self.SetState, desc="Connecting tracks to network", total=None):
            start_node = self._searchNearby(splPoint(float(track[1].longitude), float(track[1].latitude)))
            finish_node = self._searchNearby(splPoint(float(track[2].longitude), float(track[2].latitude)))

            if not start_node or not finish_node:
                continue 
            route = self.Route(start_node, finish_node)
            route['track'] = track[0]
            if safeToDb:
                db_temp.append(Path(db_session=db_session, data=route))
            result.append(route)

        if safeToDb:
            db_session.add_all(db_temp)
            db_session.commit()
        return result

    def _searchNearby(self, point):
        from graph.bounding_box import get_bounding_box
        from shapely.geometry import Point as splPoint
        bbox = get_bounding_box(point.y,  point.x, 0.5)

        nodes = (n for n,d in self.G.nodes_iter(data=True) if d['lat'] > bbox.min_latitude and \
                                                              d['lat'] < bbox.max_latitude and \
                                                              d['lon'] > bbox.min_longitude  and \
                                                              d['lon'] < bbox.max_longitude)
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
    def Route(self, startNode, endNode, routingType = None, simulatedSeason = None, simulatedDayTime = None):
        if not startNode or not endNode:
            return {"succeded" : "false", "message" : "Missing start or end point."}
        if not routingType:
            routingType = RoutingType.basic
        if not simulatedSeason: 
            simulatedSeason = Season(datetime.now())
        if not simulatedDayTime:
            simulatedDayTime = DayTime(datetime.now())
        number_of_experiments = 1
        paths_pool = {}
        for i in range(number_of_experiments):
            print("DijkstraPath experiment: %d/%d" % (i+1, number_of_experiments))
            # Set new evaluation based on probability, road type etc.
            self._ReloadGraphEvaluation(routingType, simulatedSeason, simulatedDayTime)
                
            # Compute path
            try:
                eval, path = nx.bidirectional_dijkstra(self.G, startNode, endNode, 'evaluation')
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
                    e = self.G.edge[n1][n2]
                    length += e['length']
                    edges.append({'id' : e['id'], 'length': e['length'], 'highway' :  e['highway']})

                for n in path:
                    points.append(((float(self.G.node[n]['lon']), float(self.G.node[n]['lat']))))
                paths_pool[h] = Feature(geometry=LineString(points), properties={"length" : length, "eval": eval, "count" : 1, "ids" : path, "edges" : edges})
            else:
                paths_pool[h].properties['count'] += 1

        # Set path line weight
        for path in paths_pool.values():
            path.properties['weight'] = ((path.properties['count'] * 5) / number_of_experiments) + 5
        fc = FeatureCollection([ v for v in paths_pool.values() ])
        return {"succeded" : "true", "paths" : fc, "number_of_experiments" : number_of_experiments}


    def _ReloadGraphEvaluation(self, routingType, simulatedSeason = Season(datetime.now()), simulatedDayTime = DayTime(datetime.now())):
        if routingType == RoutingType.basic:
            return
        today_diff = (datetime.now() - datetime(2015, 11, 14)).days
        today_diff = max([today_diff, 1])

        for n1, n2, edge in self.G.edges(data=True):
            if routingType == RoutingType.worstCase:
                edge['evaluation'] = edge['length'] * edge['penalty_multiplicator']
            elif routingType == RoutingType.stochasticWS or routingType == RoutingType.stochasticWad:
                pen_mul = 1
                if edge['incidents']:
                    lifetime_coefficient = len(edge['incidents']) / today_diff
                    lifetime_coefficient = min([lifetime_coefficient, 1])
                    for incident in edge['incidents']:
                        # check if total_incidents is large enaugh and time is in correlation matrix
                        if self.total_incidents > 100 and simulatedSeason in self.season_correlation and simulatedDayTime in self.daytime_correlation:
                            season_coefficient = abs(self.season_correlation[simulatedSeason][incident['season']])
                            daytime_coefficient = abs(self.daytime_correlation[simulatedDayTime][incident['daytime']])
                        else:
                            season_coefficient = SeasonCoefficient(simulatedSeason, incident['season'])
                            daytime_coefficient = DayTimeCoefficient(simulatedDayTime, incident['daytime'])
                        rnd = random()
                        probability = season_coefficient * daytime_coefficient * lifetime_coefficient
                        if rnd <= probability:
                            class_penalty = (TMCUpdateClass.ClassToPenalization[incident['class']])
                            pen_mul += class_penalty
                edge['evaluation'] = edge['length'] * pen_mul
            else:
                print('Routing type is not supported', log_type=LogType.error)



############## Depricated #####################

    def ExportFusionTables(self, fileName):
        f = fileName
        header = 'edge_id,length,n1,n1_lat,n1_lon,n2,n2_lat,n2_lon,line,color,msgs'
        _print(header,file=f)
        from ddr.database import db_session
        local_db_session = db_session()
        try:
            for n1, n2, e in get_tqdm(self.G.edges(data=True), self.SetState, desc="Exporting csv", total=None):
                msgs = '"['
                color = "ff0000"
                if len(e['msgs']) > 0:
                    color = "0000ff"
                    for m in e['msgs']:
                        m = local_db_session.merge(m)
                        msgs += '{""id"":""'+m.id+'"", ""mtxt\"":""'+ m.MTXT.value + '""},'
                    msgs = msgs[:-1]
                msgs += ']"'
                kmlLine = '"<LineString><coordinates>'+self.G.node[n1]['lon']+','+self.G.node[n1]['lat']+' '+self.G.node[n2]['lon']+','+self.G.node[n2]['lat']+'</coordinates></LineString>"' 
                _print(e['id'], e['length'],
                      n1, self.G.node[n1]['lat'], self.G.node[n1]['lon'], 
                      n2, self.G.node[n2]['lat'], self.G.node[n2]['lon'],
                      kmlLine,color,msgs,
                      sep=',', file=f)
            f.close() 
        except Exception as e:
            print(str(e), log_type=LogType.error)
            local_db_session.close()
            raise e
        local_db_session.close()