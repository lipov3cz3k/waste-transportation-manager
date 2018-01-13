from database import Base, UniqueMixin
from sqlalchemy import Column, Integer, Text, Float, Boolean


class StreetnetSections(UniqueMixin, Base):
    """ streetnet trasy """
    __tablename__ = 'StreetnetSections'

    id = Column(Integer, primary_key=True) # ROAD_ID

    length = Column(Float) # delka
    time = Column(Float) # cas
    way_name = Column(Text) # silnice
    way_class = Column(Integer) # trida_kom

    AADT_2010 = Column(Integer)
    TV_2010 = Column(Integer)
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
        return query.filter(StreetnetSections.id == kwargs['id'])

    def __repr__(self):
        return '%s' % (self.id)