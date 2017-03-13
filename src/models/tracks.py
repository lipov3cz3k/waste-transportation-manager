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
        start_address = data['start_address']
        self.start_address = Address.as_unique(kwargs['db_session'], 
                                         city=str(start_address['city']),
                                         street=str(start_address['street']) if start_address.get('street') else None,
                                         house_number=str(start_address['house_number']) if start_address.get('house_number') else None,
                                         postal=int(start_address.get('postal')) if start_address.get('postal') else None, 
                                         country=str(start_address.get('country')) if start_address.get('country') else None, 
                                         longitude=float(start_address.get('latitude')) if start_address.get('latitude') else None, 
                                         latitude=float(start_address.get('longitude')) if start_address.get('longitude') else None
                                         )
        finish_address = data['finish_address']
        self.finish_address = Address.as_unique(kwargs['db_session'], 
                                         city=str(finish_address['city']),
                                         street=str(finish_address['street']) if finish_address.get('street') else None,
                                         house_number=str(finish_address['house_number']) if finish_address.get('house_number') else None,
                                         postal=int(finish_address.get('postal')) if finish_address.get('postal') else None, 
                                         country=str(finish_address.get('country')) if finish_address.get('country') else None, 
                                         longitude=float(finish_address.get('latitude')) if finish_address.get('latitude') else None, 
                                         latitude=float(finish_address.get('longitude')) if finish_address.get('longitude') else None
                                         )
        self.start = data['start']
        self.finish = data['finish']
        self.date_from = data['date_from']
        self.date_to = data['date_to']
        self.vehicle = data['vehicle']
        self.reg_plate = data['reg_plate'] if data.get('reg_plate') else None
        self.driver = data['driver'] if data.get('driver') else None
        self.type = data['type'] if data.get('type') else None
        self.note = data['note']
        self.tank = data['tank'] if data.get('tank') else None
        self.tachometer_start = data['tachometer_start'] if data.get('tachometer_start') else None
        self.tachometer_finish = data['tachometer_finish'] if data.get('tachometer_finish') else None
        self.distance = data['distance']
        self.time = data['time']
        self.same = data['same'] if data.get('same') else None

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
    def __repr__(self):
        return '%s' % (self.id)
track_hash_index = Index('Track_hash_index', Track.hash)