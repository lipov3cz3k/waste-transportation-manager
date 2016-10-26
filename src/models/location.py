from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, UniqueConstraint, Float
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

    #coords from original source
    latitude = Column(Float)
    longitude = Column(Float)

    location_id = Column(Integer, ForeignKey('OSMLocation.obj_id'))
    location = relationship("OSMLocation")

    def __init__(self, **kwargs):
        self.hash = sha1(json.dumps(kwargs, sort_keys=True).encode("UTF-8")).hexdigest()
        return super().__init__(**kwargs)

    def set_location(self, location):
        self.location = location

    @classmethod
    def unique_hash(cls, **kwargs):
        return sha1(json.dumps(kwargs, sort_keys=True).encode("UTF-8")).hexdigest()

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(Address.hash == sha1(json.dumps(kwargs, sort_keys=True).encode("UTF-8")).hexdigest())
address_coords_index = Index('Address_coords_index', Address.latitude, Address.longitude)

class OSMLocation(UniqueMixin, Base) :
    __tablename__ = 'OSMLocation'
    obj_id = Column(Integer, primary_key=True)

    city = Column(Text)
    village = Column(Text)
    town = Column(Text)
    hamlet = Column(Text)
    house_number = Column(Text)
    country = Column(Text)
    postcode = Column(Text)
    road = Column(Text)
    latitude = Column(Text)
    longitude = Column(Text)
    osm_id = Column(Text)

    def __init__(self, **kwargs):
        self.osm_id = kwargs['osm_id']
        self.latitude = kwargs['latitude']
        self.longitude = kwargs['longitude']
        address = kwargs['address']
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
    def unique_hash(cls, **kwargs):
        return kwargs['osm_id']

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(OSMLocation.osm_id == kwargs['osm_id'])

location_osm_id_index = Index('Location_osm_id_index', OSMLocation.osm_id)
location_road_index = Index('Location_road_index', OSMLocation.road)