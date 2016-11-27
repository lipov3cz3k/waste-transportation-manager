from iso8601 import parse_date
from common.alertc import TMCUpdateClass
from common.utils import Season, DayTime
from common.config import local_config
from xml.sax.handler import ContentHandler
from xml.sax import SAXException
from sqlalchemy import inspect

class Node:
    def __init__(self, id, lon, lat, tags = {}):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.tags = tags

class Way:

    def __init__(self, id, nodes = [], tags = {}):
        self.id = id
        self.nodes = nodes
        self.tags = tags
        self.msgs = []
        self.containers = []
        self.length = 0
        self.forward = None

    def GetFirstLastNodeId(self):
        return (self.nodes[0], self.nodes[-1])

    def GetIncidents(self, db_session):
        from ddr.ddr_models import TSTA, MTIME, MEVT, TSTO, EVI
        incidents = []
        for msg in self.msgs:
            if inspect(msg).detached:
                msg = db_session.merge(msg)
            if msg.type == 'TI':
                #TSTA =  msg.MTIME.TSTA.value
                tsta = db_session.query(TSTA.value).filter(msg.MTIME_id == MTIME.obj_id,
                                                           MTIME.TSTA_id == TSTA.obj_id).limit(1).one()
                tsta = tsta.value
                if not any(d.get('TSTA', None) == tsta for d in incidents):
                    daytime = parse_date(tsta)
                    #evi = msg.MEVT.TMCE.EVI
                    evi = db_session.query(EVI).filter(msg.MEVT_id == MEVT.obj_id,
                                                       MEVT.TMCE_id == EVI.TMCE_id).limit(3).all()

                    worstTMCclass = TMCUpdateClass.NONE
                    for e in evi:
                        for tmcClass, tmcPen in TMCUpdateClass.ClassToPenalization.items():
                            if int(e.updateclass) == tmcClass:
                                worstTMCclass = tmcClass if TMCUpdateClass.ClassToPenalization[worstTMCclass] < tmcPen else worstTMCclass

                    tsto = db_session.query(TSTO.value).filter(msg.MTIME_id == MTIME.obj_id,
                                                               MTIME.TSTO_id == TSTO.obj_id).limit(1).one()
                    tsto = tsto.value
                    incidents.append({'class' : worstTMCclass, 'TSTA' : tsta, 'TSTO' : tsto, 'season' : Season(daytime), 'daytime' : DayTime(daytime)})
        return incidents

    def GetContainers(self, db_session, right_side = None):
        containers = []
        for container, direction in self.containers:
            if inspect(container).detached:
                container = db_session.merge(container)
            if container.address.latitude:
                coords = (container.address.latitude, container.address.longitude)
            elif container.address.location:
                coords = (container.address.location.latitude, container.address.location.longitude)
            else:
                continue
            if right_side != None:
                if (self.forward == direction['right_side']) != right_side:
                    continue

            containers.append({'id' : container.id, 
                               'container_type' : container.container_type, 
                               'waste_code' : container.waste_code, 
                               'lat' : coords[0], 
                               'lon' : coords[1],
                               'quantity' : container.quantity,
                               'capacity' : container.capacity,
                               'interval' : container.interval })
        return containers

    def reductive_split(self, dividers):
        def slice_array(ar, dividers):
            result = []
            right = None
            for node in ar[1:-1]:
                if dividers[node.id] > 1:
                    left = ar[:ar.index(node)+1]
                    right = ar[ar.index(node):]
                    result += [left]
                    ar = right

            if right:
                result += [right]

            if len(result) == 0:
                result = [ar]

            return result
        slices = slice_array(self.nodes, dividers)

        # create a way object for each node-array slice
        ret = []
        i=0
        for slice in slices:
            new_id = "%s-%d" % (self.id, i)
            new_way = Way(new_id)
            new_way.nodes = slice
            new_way.tags = self.tags
            ret.append( new_way )
            i += 1
        return ret

    def set_direction(self):
        self.forward = self.nodes[0].lat < self.nodes[1].lat
        self.forward = True if self.nodes[0].lat == self.nodes[1].lat and self.nodes[0].lon < self.nodes[1].lon else self.forward

class SimpleHandler(ContentHandler):

    def __init__(self, node_histogram, ways, total_size, SetStateFc, run):
        ContentHandler.__init__(self)
        self.id = None
        self.lon = None
        self.lat = None
        self.nodes = []
        self.tags = {}

        self.allowed_tags = None

        self.nodes_global = {}
        self.node_histogram = node_histogram
        self.ways_global = ways

        self.total_size = total_size
        self.SetStateFc = SetStateFc
        self.run = run
        self.percentage = 0

    def TestIsRun(self):
        if not self.run[0]:
            raise SAXException("Service not running")

    def startElement(self, name, attrs):
        self.TestIsRun()
        percentage = int((float(self._locator._ref._source._InputSource__bytefile.raw.tell())/self.total_size)*100)
        if self.percentage != percentage:
            self.percentage = percentage
            self.SetStateFc(percentage=self.percentage)
        if name == 'node':
            self.id = attrs['id']
            self.lon = attrs['lon']
            self.lat = attrs['lat']
            self.tags = {}
            self.allowed_tags = local_config.allowed_tags_node
        elif name == 'way':
            self.id = attrs['id']
            self.nodes = []
            self.tags = {}
            self.allowed_tags = local_config.allowed_tags_way
        elif name == 'tag':
            if attrs['k'] in self.allowed_tags:
                if (attrs['k'] != "oneway") or (attrs['k'] == "oneway" and attrs['v'] == "yes"):
                    self.tags[attrs['k']] = attrs['v']
        elif name == 'nd':
            self.nodes.append(self.nodes_global[attrs['ref']])
            self.node_histogram[attrs['ref']] += 1

    def endElement(self, name):
        if name == 'node':
            self.nodes_global[self.id] = Node(self.id, self.lon, self.lat, self.tags)
            self.node_histogram[self.id] = 0
            self.reset()
        elif name == "way":
            if len(self.nodes) > 1:
                self.ways_global[self.id] = Way(self.id, self.nodes, self.tags)
            self.reset()

    def reset(self):
        self.id = None
        self.lon = None
        self.lat = None
        self.nodes = []
        self.tags = {}
        self.allowed_tags = None
