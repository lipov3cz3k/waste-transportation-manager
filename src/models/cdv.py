from database import Base, UniqueMixin
from sqlalchemy import Column, Integer, Text, Float, Boolean


class StreetnetSegments(UniqueMixin, Base):
    """ streetnet useky """
    __tablename__ = 'StreetnetSegments'

    id = Column(Integer, primary_key=True) # ROAD_ID
    length = Column(Float) # delka
    time = Column(Float) # cas
    way_name = Column(Text) # silnice
    way_class = Column(Integer) # trida_kom

    AADT_2010 = Column(Integer) # Annual average daily traffic
    TV_2010 = Column(Integer) # Truck vehicles
    bridge = Column(Boolean) # most
    underpass = Column(Boolean) # podjezd
    tunnel = Column(Boolean) # tunel

    min_load_capacity = Column(Float) # MIN_nosnost
    min_height = Column(Float) # MIN_vyska
    start_X = Column(Float)
    start_Y = Column(Float)
    end_X = Column(Float)
    end_Y = Column(Float)

    @classmethod
    def unique_hash(cls, **kwargs):
        return kwargs['id']

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(StreetnetSegments.id == kwargs['id'])

    def __repr__(self):
        return '%s' % (self.id)

class StreetnetOSMRelation(Base):
    __tablename__ = 'StreetnetOSMRelation'

    id = Column(Integer, primary_key=True)
    version = Column(Integer)
    streetnet_id = Column(Integer)
    osm_way_id = Column(Integer)
