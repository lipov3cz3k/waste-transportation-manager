from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import relationship, backref
from database import Base

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

location_osm_id_index = Index('Location_osm_id_index', Location.osm_id)