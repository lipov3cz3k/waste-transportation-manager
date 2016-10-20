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

@DECORATE_ALL(TRACE_FN_CALL)
class Network:
    def __init__(self, state = None, run = {0: False}):
        self.state = state
        self.graphID = None
        self.max_penalty = 0
        self.G = nx.DiGraph()
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
            osm = OSMParser(self.graphID, state=self.state, run=self.run)
            osm.ParseFromXMLFile(osm_path_xml_data)
#            osm.ConnectDDRDataWithWays(db_session)
            osm.ConnectContainersWithWays(db_session)
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
            self.fillGraphWithData(osm, db_session)
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

    def fillGraphWithData(self, osm, db_session):
        for id, uniq_w in get_tqdm(osm.ways.items(), self.SetState, desc="Add edges to graph, compute evaluation", total=None):
            for w in uniq_w:
                self.TestIsRun()
                incidents = w.GetIncidents(db_session)
                self.total_incidents += len(incidents)
                penalty_multiplicator = GetPenaltyMul(incidents)
                if penalty_multiplicator > self.max_penalty:
                    self.max_penalty = penalty_multiplicator
                params = {'id':w.id, 'length':w.length, 'msgs':w.msgs, 'incidents':incidents, 'penalty_multiplicator':penalty_multiplicator, 'containers' : w.GetContainers(db_session)}
                node_first, node_last = w.GetFirstLastNodeId()
                self.G.add_path((node_first.id, node_last.id), **params)

                if ('oneway' not in w.tags and w.tags['highway'] != 'motorway') or ('oneway' in w.tags and w.tags['oneway'] != 'yes' and w.tags['oneway'] != '-1' and w.tags['highway'] != 'motorway'):
                    self.G.add_path((node_last.id, node_first.id), **params)

                self.G.node[node_first.id] = dict(lon=node_first.lon, lat=node_first.lat)
                self.G.node[node_last.id] = dict(lon=node_last.lon, lat=node_last.lat)

            osm.ways[id] = None
        
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
        return self.G.edges()

    def GetNodesGeoJSON(self):
        features = []
        for n_id in self.G.nodes_iter():
            features.append( Feature(id=n_id, geometry=Point((float(self.G.node[n_id]['lon']), float(self.G.node[n_id]['lat'])))) )
        return FeatureCollection(features)

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
        from ddr.database import db_session
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
        
        with open(file_path+"_n.csv", 'w') as f:
            writer = csv.writer(f)
            writer.writerows([self.GetNodes()])

        
        return self.GetNodes()


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


    def DijkstraPath(self, startNode, endNode, routingType = RoutingType.stochasticWS, simulatedSeason = Season(datetime.now()), simulatedDayTime = DayTime(datetime.now())):
        if not startNode or not endNode:
            return {'succeded' : False, 'message' : 'Missing start or end point.'}

        today_diff = (datetime.now() - datetime(2015, 11, 14)).days
        today_diff = max([today_diff, 1])
        number_of_experiments = 1
        paths_pool = {}
        if routingType == RoutingType.stochasticWad:
            number_of_experiments = local_config.number_of_stochastic_experiments
        
        for i in range(number_of_experiments):
            print("DijkstraPath experiment: %d/%d" % (i+1, number_of_experiments))
            # Set new evaluation based on probability, road type etc.
            for n1, n2, edge in self.G.edges(data=True):
                if routingType == RoutingType.stochasticWS or routingType == RoutingType.stochasticWad:
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
                else: # deterministic
                    if routingType == RoutingType.worstCase:
                        edge['evaluation'] = edge['length'] * edge['penalty_multiplicator']
                    else:
                        edge['evaluation'] = edge['length']
            

            try:
                eval, path = nx.bidirectional_dijkstra(self.G, startNode, endNode, 'evaluation')
            except nx.NetworkXNoPath as e:
                return {'succeded' : False, 'message' : str(e.args[0])}
            except nx.NetworkXError as e:
                return {'succeded' : False, 'message' : str(e.args[0])}

            h = hash(tuple(path))
            if not h in paths_pool:
                points = []
                length = 0
                for n1,n2 in zip(path[0:], path[1:]):
                    length += self.G.edge[n1][n2]['length']

                for n in path:
                    points.append(((float(self.G.node[n]['lon']), float(self.G.node[n]['lat']))))
                paths_pool[h] = Feature(geometry=LineString(points), properties={"length" : length, "eval": eval, "count" : 1})
            else:
                paths_pool[h].properties['count'] += 1
        for path in paths_pool.values():
            path.properties['weight'] = ((path.properties['count'] * 5) / number_of_experiments) + 5

        fc = FeatureCollection([ v for v in paths_pool.values() ])
        return {'succeded' : True, 'paths' : fc, 'number_of_experiments' : number_of_experiments}