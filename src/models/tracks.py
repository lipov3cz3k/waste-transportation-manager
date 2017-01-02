from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, DateTime, String, Time
from sqlalchemy.orm import relationship, backref
from database import Base, UniqueMixin
from models.location import Address
from hashlib import sha1

class Track(UniqueMixin, Base) :
    __tablename__ = 'Track'
    id = Column(Integer, primary_key=True)
    hash = Column(Integer, unique=True, nullable=False)

    start = Column(Text)
    finish = Column(Text)

    start_id = Column(Integer, ForeignKey('Address.id'))
    start_address = relationship("Address", foreign_keys=[start_id])

    finish_id = Column(Integer, ForeignKey('Address.id'))
    finish_address = relationship("Address", foreign_keys=[finish_id])

    date_from = Column(DateTime)
    date_to = Column(DateTime)
    vehicle = Column(Text)
    reg_plate = Column(Text)
    driver = Column(Text)
    type = Column(Text)
    note = Column(Integer)
    tank = Column(Integer)
    tachometer_start = Column(Integer)
    tachometer_finish = Column(Integer)
    distance = Column(Integer)
    time = Column(Time)
    same = Column(Integer)

    def __init__(self, **kwargs):
        data = kwargs['data']
        if data == None :
            return

        s = sha1()
        s.update(data['date_from'].isoformat().encode('utf-8'))
        s.update(data['date_to'].isoformat().encode('utf-8'))
        s.update(str(data['distance']).encode('utf-8'))
        self.hash = s.hexdigest()

        self.start_address = Address.as_unique(kwargs['db_session'], 
                                         city=str(data['start_address']['city']),
                                         street=str(data['start_address']['street']),
                                         house_number=str(data['start_address']['house_number']), 
                                         longitude=float(data.get('latitude')) if data.get('latitude') else None, 
                                         latitude=float(data.get('longitude')) if data.get('longitude') else None
                                         )
        self.finish_address = Address.as_unique(kwargs['db_session'], 
                                         city=str(data['finish_address']['city']),
                                         street=str(data['finish_address']['street']),
                                         house_number=str(data['finish_address']['house_number']), 
                                         longitude=float(data.get('latitude')) if data.get('latitude') else None, 
                                         latitude=float(data.get('longitude')) if data.get('longitude') else None
                                         )
        self.start = data['start']
        self.finish = data['finish']
        self.date_from = data['date_from']
        self.date_to = data['date_to']
        self.vehicle = data['vehicle']
        self.reg_plate = data['reg_plate']
        self.driver = data['driver']
        self.type = data['type']
        self.note = data['note']
        self.tank = data['tank']
        self.tachometer_start = data['tachometer_start']
        self.tachometer_finish = data['tachometer_finish']
        self.distance = data['distance']
        self.time = data['time']
        self.same = data['same']

    @classmethod
    def unique_hash(cls, **kwargs):
        data = kwargs['data']
        s = sha1()
        s.update(data['date_from'].isoformat().encode('utf-8'))
        s.update(data['date_to'].isoformat().encode('utf-8'))
        s.update(str(data['distance']).encode('utf-8'))
        return s.hexdigest()

    @classmethod
    def unique_filter(cls, query, **kwargs):
        data = kwargs['data']
        s = sha1()
        s.update(data['date_from'].isoformat().encode('utf-8'))
        s.update(data['date_to'].isoformat().encode('utf-8'))
        s.update(str(data['distance']).encode('utf-8'))
        return query.filter(Track.hash == s.hexdigest())
track_hash_index = Index('Track_hash_index', Track.hash)