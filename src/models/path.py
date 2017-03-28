from database import Base
import datetime
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, DateTime, String, Time
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.orderinglist import ordering_list
from models.location import Address
from models.tracks import Track

class Path(Base):
    __tablename__ = 'Path'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    track_id = Column(Integer, ForeignKey('Track.id'))
    track = relationship("Track", foreign_keys=[track_id])

    routes = relationship("Routes", order_by="Routes.position",
                            collection_class=ordering_list('position'))

    configuration = Column(Text)
    def __init__(self, **kwargs):
        route = kwargs['data']
        self.track = route['track']
        if route['succeded'] == 'true':
            properties = route.get('paths').get('features')[0].get('properties')
            ids = properties.get('ids')
            i = 0
            for start, end in zip(ids, ids[1:]):
                edge = properties.get('edges')[i]
                self.routes.append(Routes(start_node_id = start, end_node_id = end, 
                                          path_id = id, highway = edge.get('highway'), 
                                          length = edge.get('length'),
                                          segment_id = edge.get('id')))
                i += 1
            

class Routes(Base):
    __tablename__ = 'Routes'

    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey('Path.id'))
    
    start_node_id = Column(Integer, ForeignKey('Address.id'))
    start_node = relationship("Address", foreign_keys=[start_node_id])

    end_node_id = Column(Integer, ForeignKey('Address.id'))
    end_node = relationship("Address", foreign_keys=[end_node_id])
    
    position = Column(Integer)
    length = Column(Integer)
    highway = Column(String)
    segment_id = Column(String)

