from _socket import error
from pickle import dump as pickle_dump, load as pickle_load
from geopy.distance import vincenty
from os.path import join, exists, getsize
from shapely.geometry import LineString, Point
from common.config import local_config
from common.utils import LogType, print, TRACE_FN_CALL, DECORATE_ALL, get_tqdm
from .elements import SimpleHandler
from xml.sax import make_parser
from multiprocessing.pool import ThreadPool


#@DECORATE_ALL(TRACE_FN_CALL)
class OSMParser:

    def __init__(self, graphID, bbox, state, run = {0: False}):
        print("Initialize OSM Parser", LogType.info)
        self.ways = {}
        self.streetNames = {}
        self.graphID = graphID
        self.node_histogram = {}
        self.bbox = bbox
        self.state = state
        self.city_nodes = {}
        self.relations = {}
        self.run = run

        self.last_location_obj_id = 0 # last location for last message which was connected with graph


    def TestIsRun(self):
        if not self.run[0]:
            raise Exception("Service not running")

    def SetState(self, action = None, percentage = None):
        if action != None and action == self.state['action'] and percentage <= self.state['percentage']:
            return

        if action != None:
            self.state['action'] = action
        if percentage != None:
            self.state['percentage'] = int(percentage)

    def SaveToFile(self, file_path = None):
        if not file_path:
            file_path = join(local_config.folder_graphs_root, '%s.o' % self.graphID)
        with open(file_path, 'wb') as output:
            pickle_dump(self.__dict__, output)

    def LoadFromFile(self, graphID):
        tmp_graphID = self.graphID
        file_path = join(local_config.folder_graphs_root, '%s.o' % graphID)

        if not exists(file_path):
            raise FileNotFoundError("Cannot find \"%s\". Run GRAPH first" % (file_path))
        with open(file_path, 'rb') as input:
            tmp_dict = pickle_load(input)
            self.__dict__.update(tmp_dict)

        self.graphID = tmp_graphID

    def ParseFromXMLFile(self, osm_path_xml_data):
        print("Parse OSM data.")
        self.ParseOSMData(osm_path_xml_data)

        print("Split ways by intersections and remove unused nodes")

        self.ways = self.SplitWaysByIntersectionsRemoveUnusedNodes()
        self.node_histogram = None

    def ParseOSMData(self, osm_path_xml_data):
        self.SetState(action="Parse OSM Data", percentage=0)
        try:
            total_size = getsize(osm_path_xml_data)
            parser = make_parser()
            parser.setContentHandler(SimpleHandler(self.node_histogram, self.ways, self.relations, self.city_nodes, total_size, self.SetState, self.run))
            city_xml_data = osm_path_xml_data+'.city'
            print("parsing path xml")
            with open(osm_path_xml_data, 'rb') as osm_data:
                parser.parse(osm_data)
            print("parsing city xml")
            with open(city_xml_data, 'rb') as osm_data:
                parser.parse(osm_data)
        except Exception as e:
            print("Cannot read or parse stored OSM data file: %s" % str(e), LogType.error)
            raise Exception("")
        self.SetState(action="Parse OSM Data", percentage=100)

    def SplitWaysByIntersectionsRemoveUnusedNodes(self):
        #use that histogram to split all ways, replacing the member set of ways
        new_ways = {}
        for id, way in get_tqdm(self.ways.items(), self.SetState, desc="Splitting edges", total=None):
            self.TestIsRun()
            split_ways = way.reductive_split(self.node_histogram)
            new_ways[way.id] = []
            if 'name' in way.tags:
                self.streetNames.setdefault(way.tags.get('name'), []).append(way.id)
            for split_way in split_ways:

                first, last = split_way.GetFirstLastNodeId()
                distance = 0
                past = first
                for current in split_way.nodes:
                    distance += vincenty((past.lat, past.lon), (current.lat, current.lon)).meters
                    past = current
                split_way.length = round(distance)
                split_way.set_direction()
                new_ways[way.id].append(split_way)

        return new_ways




    ################## DDR traffic info #####################

    def ConnectDDRDataWithWays(self, db_session):
        from ddr.ddr_models import Location, MSG, COORD
        print("Connect DDR Data with ways")
        msgs_count_total = 0
        locations_count_total = 0


        thread_pool = ThreadPool(processes=local_config.thread_pool_size_for_mapping)
        thread_results = {}

        div_mod = divmod(len(self.ways), 998)
        start = 0

        iteration_total = div_mod[0]
        if div_mod[1] != 0:
            iteration_total += 1

        print("Getting locations and starts thread")
        self.SetState(action="Mapping transport info (DDR)", percentage=0)
        for x in range(div_mod[0]):
            self.TestIsRun()
            in_ways = list(self.ways.keys())[start:start+998]
            locations = db_session.query(Location.obj_id, Location.osm_id, MSG, COORD.x, COORD.y).filter(Location.osm_id.in_(in_ways),
                                                                                                  Location.obj_id > self.last_location_obj_id,
                                                                                                  MSG.Location_id == Location.obj_id,
                                                                                                  COORD.Location_id == Location.obj_id).all()
            if len(locations) != 0:
                thread_pool.apply_async(self.ConnectMSGfromLocations, args=(locations, x, iteration_total, thread_results))
                locations_count_total += len(locations)

            start += 998
        else:
            in_ways = list(self.ways.keys())[-1*div_mod[1]:]
            locations = db_session.query(Location.obj_id, Location.osm_id, MSG, COORD.x, COORD.y).filter(Location.osm_id.in_(in_ways),
                                                                                                  Location.obj_id > self.last_location_obj_id,
                                                                                                  MSG.Location_id == Location.obj_id,
                                                                                                  COORD.Location_id == Location.obj_id).all()
            if len(locations) != 0:
                thread_pool.apply_async(self.ConnectMSGfromLocations, args=(locations, iteration_total, iteration_total, thread_results))
                locations_count_total += len(locations)

        print("Threads started, wait for finish.")
        thread_pool.close()
        thread_pool.join()
        print("Threads finished.")
        self.SetState(action="Mapping transport info (DDR)", percentage=100)
        self.TestIsRun()

        for k, v in thread_results.items():
            msgs_count_total += v['msgs_count']
            if v['last_location_obj_id'] > self.last_location_obj_id:
                self.last_location_obj_id = v['last_location_obj_id']

        print("Messages total: %s" % msgs_count_total)
        print("Connecting finished")
        return msgs_count_total

    def ConnectMSGfromLocations(self, locations, iteration, iteration_total, thread_results):
        from ddr.ddr_models import MEVT, EVI
        from ddr.database import db_session
        local_db_session = db_session()
        msgs_count = 0
        last_location_obj_id = 0

        try:
            print("[%d] Mapping %s locations" % (iteration, len(locations)))
            self.SetState(action="Mapping transport info (DDR)", percentage=int((iteration/iteration_total)*100))
            for location in locations:
                self.TestIsRun()
                location_obj_id, location_osm_id, msg, coord_x, coord_y = location
                if location_obj_id > last_location_obj_id:
                    last_location_obj_id = location_obj_id
                way_id = location_osm_id

                if msg:
                    evi = local_db_session.query(EVI).filter(msg.MEVT_id == MEVT.obj_id,
                                                       MEVT.TMCE_id == EVI.TMCE_id).limit(3).all()
                    has_allowed_evi = True
                    for e in evi:
                        if int(e.updateclass) in local_config.not_allowed_evi:
                            has_allowed_evi = False
                            break
                    if not has_allowed_evi:
                        continue

                    msgs_count += 1
                    ways = self.ways[way_id]
                    if len(ways) == 1:
                        ways[0].msgs.append(msg)
                    elif len(ways) > 1:
                        ways_min_distance = {}
                        for way in ways:
                            min_distance = None

                            for node in way.nodes:
                                distance = vincenty((coord_y, coord_x), (node.lon, node.lat)).meters
                                if min_distance is None or min_distance > distance:
                                    min_distance = distance

                            ways_min_distance[way] = min_distance

                        min_value = min(ways_min_distance.values())
                        min_keys = [k for k in ways_min_distance if ways_min_distance[k] == min_value]
                        if len(min_keys) == 1:
                            min_keys[0].msgs.append(msg)
                        elif len(min_keys) > 1:
                            # TODO: decide which way!!!!
                            for way in min_keys:
                                way.msgs.append(msg)
        except Exception as e:
            print(str(e), log_type=LogType.error)
            local_db_session.close()
            raise e

        thread_results[iteration] = {'msgs_count': msgs_count, 'last_location_obj_id': last_location_obj_id}
        print("[%d] Mapping finished" % (iteration))
        local_db_session.close()

    def _cut(self, line, distance, nodes=None):
        # Cuts a line in two at a distance from its starting point
        if distance <= 0.0 or distance >= line.length:
            return ([LineString(line)],len(line.coords)-1)
        coords = list(line.coords)
        for i, p in enumerate(coords):
            pd = line.project(Point(p))
            if pd == distance:
                return ([
                         LineString(coords[:i+1]),
                         LineString(coords[i:])],
                        i)
            if pd > distance:
                cp = line.interpolate(distance)
                return ([
                         LineString(coords[:i+1]),
                         LineString([(cp.x, cp.y)] + coords[i:])],
                        i)
        return ([LineString(line)],len(line.coords)-1)

    def _Geometry(self, way):
        x = [(float(node.lon), float(node.lat)) for node in way.nodes]
        if len(x) >= 2:
            return LineString(x)
        else:
            return Point(x[0])

    def _Direction(self, way, point, point_id=None):
        direction = None
        try:
            ls = self._Geometry(way)
            part, cut_id = self._cut(ls, ls.project(point))
            closestSeg = way.nodes[cut_id-1], way.nodes[cut_id]
            a_point = float(closestSeg[0].lon), float(closestSeg[0].lat)
            b_point = float(closestSeg[1].lon), float(closestSeg[1].lat)
            p_to_a = point.distance(Point(a_point))
            p_to_b = point.distance(Point(b_point))
            close,far = (a_point, b_point) if p_to_a < p_to_b else (b_point, a_point)
            p = point.coords[0]

            kriterium = (close[1]-far[1])*(p[0]-close[0])+(far[0]-close[0])*(p[1]-close[1])

            start,end = (way.nodes[0].id, way.nodes[-1].id) if p_to_a < p_to_b else (way.nodes[-1].id, way.nodes[0].id)
            if kriterium < 0:
                direction = (start, end)
                print("(%s) %s -> %s" % (point_id, start, end))
            elif kriterium > 0:
                direction = (end, start)
                print("(%s) %s -> %s" % (point_id, end, start))
            else:
                print("cannot determine direction")
        except Exception as e:
            print("Direction detection failed", log_type=LogType.error)
            raise e
        return direction

    ################## Waste management #####################
    def ConnectContainersWithWays(self, db_session):
        print("Connect waste containers with ways")

        from models.waste import Container
        from models.location import Address, OSMLocation
        from database import db_session
        local_db_session = db_session()
        optimalization = True
        dist = lambda way: point.distance(self._Geometry(way))
        all_ways = [item for sublist in self.ways.values() for item in sublist]
        containers_obj = local_db_session.query(Container).join(Address) \
                                                          .join(Address.location) \
                                                          .filter((Address.latitude > self.bbox.min_latitude) | (OSMLocation.latitude > self.bbox.min_latitude)) \
                                                          .filter((Address.latitude < self.bbox.max_latitude) | (OSMLocation.latitude < self.bbox.max_latitude)) \
                                                          .filter((Address.longitude > self.bbox.min_longitude) | (OSMLocation.longitude > self.bbox.min_longitude)) \
                                                          .filter((Address.longitude < self.bbox.max_longitude) | (OSMLocation.longitude < self.bbox.max_longitude)) \
                                                          .all()
        if len(containers_obj) == 0:
            return

        try:
            #print("[%d] Mapping %s containers" % (iteration, len(containers_obj)))
            #self.SetState(action="Mapping containers", percentage=int((iteration/iteration_total)*100))
            for container in get_tqdm(containers_obj, self.SetState, desc="Connecting containers to streets", total=None):
            #for container in containers_obj:
                self.TestIsRun()
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
                    print("Address %s %s, %s has no OSM equivalent, skipping." % (container.address.street, container.address.house_number, container.address.city), LogType.warning)
                    continue

                if not self.bbox.InBoundingBox(point.x, point.y):
                    print("Address %s %s, %s is out of mapping area, skipping." % (container.address.street, container.address.house_number, container.address.city), LogType.info)
                    continue

                wanted_keys = self.streetNames.get(street)
                if wanted_keys is None or not optimalization:
                    if not optimalization:
                        print("Address %s %s, %s has no road loading all roads." % (container.address.street, container.address.house_number, container.address.city), LogType.info)
                    ways = all_ways
                else:
                    ways = [self.ways[x] for x in wanted_keys]
                    ways = [item for sublist in ways for item in sublist]

                if len(ways) == 1:
                    direction = self._Direction(ways[0], point, container.id)
                    ways[0].containers.append((container, direction))
                elif len(ways) > 1:
                    near_way = min(ways, key=dist)
                    direction = self._Direction(near_way, point, container.id)
                    near_way.containers.append((container, direction))
                
        except Exception as e:
            print(str(e), log_type=LogType.error)
            local_db_session.close()
            raise e
        local_db_session.close()



    ################## Boundary shape  #####################


    def GetLAU2Shapes(self):
        from shapely.geometry import MultiLineString, LineString

        print("Creating shapes from OSM relation objects")
        result = {}
        for k, rel in self.relations.items():
            if not 'admin_level' in rel.tags:
                continue
            if rel.tags['admin_level'] != '8':
                continue

            ls = []
            for way in rel.ways:
                ls.append(LineString(tuple([(float(node.lat), float(node.lon)) for node in way.nodes])))
            
            ml = MultiLineString(ls).convex_hull
            
            result[k] = {'id' : k, 'shape' : ml, 'tags' : rel.tags, 'admin_centre' : rel.admin_centre}
        return result
                    
                    
                

            