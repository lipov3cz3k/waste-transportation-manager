from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, DateTime, String, Time
from sqlalchemy.orm import relationship, backref
from database import Base, UniqueMixin
from hashlib import sha1

class Track(Base) :
    __tablename__ = 'Track'
    id = Column(Integer, primary_key=True)

    start = Column(Text)
    finish = Column(Text)
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
