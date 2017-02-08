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
            for node in route.get('paths').get('features')[0].get('properties').get('ids'):
                self.routes.append(Routes(node_id = node, path_id = id))        
        

class Routes(Base):
    __tablename__ = 'Routes'

    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey('Path.id'))
    
    node_id = Column(Integer, ForeignKey('Address.id'))
    node = relationship("Address", foreign_keys=[node_id])
    position = Column(Integer)

