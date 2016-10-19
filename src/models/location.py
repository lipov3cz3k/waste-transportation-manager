from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from database import Base, UniqueMixin
from hashlib import sha1
import json

class Address(UniqueMixin, Base) :
    __tablename__ = 'Address'
    id = Column(Integer, primary_key=True)

    city = Column(Text)
    street = Column(Text)
    house_number = Column(Text)
    hash = Column(Integer, unique=True, nullable=False)

    location_id = Column(Integer, ForeignKey('Location.obj_id'))
    location = relationship("Location")

    def __init__(self, **kwargs):
        self.hash = sha1(json.dumps(kwargs, sort_keys=True).encode("UTF-8")).hexdigest()
        return super().__init__(**kwargs)

    @classmethod
    def unique_hash(cls, **kwargs):
        return sha1(json.dumps(kwargs, sort_keys=True).encode("UTF-8")).hexdigest()

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(Address.hash == sha1(json.dumps(kwargs, sort_keys=True).encode("UTF-8")).hexdigest())

class Location(UniqueMixin, Base) :
    __tablename__ = 'Location'
    obj_id = Column(Integer, primary_key=True)

    city = Column(Text)
    village = Column(Text)
    town = Column(Text)
    hamlet = Column(Text)
    house_number = Column(Text)
    country = Column(Text)
    postcode = Column(Text)
    road = Column(Text)
    osm_id = Column(Text)

    def __init__(self, address=None, osm_id=None):
        self.osm_id = osm_id

        if 'city' in address:
            self.city = address['city']
        if 'village' in address:
            self.village = address['village']
        if 'town' in address:
            self.town = address['town']
        if 'hamlet' in address:
            self.hamlet = address['hamlet']
        if 'house_number' in address:
            self.house_number = address['house_number']
        if 'country' in address:
            self.country = address['country']
        if 'postcode' in address:
            self.postcode = address['postcode']
        if 'road' in address:
            self.road = address['road']

    @classmethod
    def unique_hash(cls, osm_id):
        return osm_id

    @classmethod
    def unique_filter(cls, query, osm_id):
        return query.filter(Location.osm_id == osm_id)

location_osm_id_index = Index('Location_osm_id_index', Location.osm_id)