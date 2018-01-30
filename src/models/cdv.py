from database import Base, UniqueMixin
from sqlalchemy import Column, Integer, Text, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship, backref


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
    start_longitude = Column(Float)
    start_latitude = Column(Float)
    end_longitude = Column(Float)
    end_latitude = Column(Float)

    OSMRelations = relationship("StreetnetOSMRelation", cascade="all", backref="StreetnetSegments")


    @classmethod
    def unique_hash(cls, **kwargs):
        return kwargs['id']

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(StreetnetSegments.id == kwargs['id'])

    def __repr__(self):
        return '%s' % (self.id)

segments_start_coords_index = Index('Segments_start_coords_index', StreetnetSegments.start_latitude, StreetnetSegments.start_longitude)
segments_end_coords_index = Index('Segments_end_coords_index', StreetnetSegments.end_latitude, StreetnetSegments.end_longitude)

class StreetnetOSMRelation(Base):
    __tablename__ = 'StreetnetOSMRelation'

    id = Column(Integer, primary_key=True)
    version = Column(Integer)
    streetnet_id = Column(Integer, ForeignKey('StreetnetSegments.id'))
    streetnet = relationship("StreetnetSegments")
    osm_way_id = Column(Text)
