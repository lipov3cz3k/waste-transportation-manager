from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import relationship, backref
from database import Base
from models.location import Location

def get_attribute(root, key, repeatable = False) :
    if isinstance(key, str) :
        return root.get(key, default=None)
    elif isclass(key) :
        if not repeatable :
            return key(root.find(key.__name__)) if root.find(key.__name__) != None else None
        else :
            return [key(xml_tmp) for xml_tmp in root.findall(key.__name__) if xml_tmp != None]


"""
Class represents document
get XML in constructor
read attributes from XML or create "subclass" (vnorene objekty)
"""
class DOC(Base) :
    """zapouzdřuje celý dokument pro výměnu informací"""
    __tablename__ = 'DOC'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    file_name = Column(Text)

    version = Column(Text)
    id = Column(Text)
    country = Column(Text)
    DataSet = Column(Text)

    INF_id = Column(Integer, ForeignKey('INF.obj_id'))
    INF = relationship("INF", backref=backref('DOC', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    MJD_id = Column(Integer, ForeignKey('MJD.obj_id'))
    MJD = relationship("MJD", backref=backref('DOC', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml=None, file_name=None):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.file_name = file_name

        self.version = get_attribute(root_xml, "version")
        self.id = get_attribute(root_xml, "id")
        self.country = get_attribute(root_xml, "country")
        self.DataSet = get_attribute(root_xml, "DataSet")

        self.INF = get_attribute(root_xml, INF)
        self.MJD = get_attribute(root_xml, MJD)

    def __repr__(self):
        return '<DOC %r>' % (self.id)

class INF(Base) :
    """Informace o subjektech, které si vyměňují XML dokument"""
    __tablename__ = 'INF'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    sender = Column(Text)
    receiver = Column(Text)
    transmission = Column(Text)

    DAT_id = Column(Integer, ForeignKey('DAT.obj_id'))
    DAT = relationship("DAT", backref=backref('INF', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.sender = get_attribute(root_xml, "sender")
        self.receiver = get_attribute(root_xml, "receiver")
        self.transmission = get_attribute(root_xml, "transmission") 

        self.DAT = get_attribute(root_xml, DAT)

class DAT(Base) :
    """TAG zapouzdřující informace o verzích jednotlivých datových sad"""
    __tablename__ = 'DAT'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    EVTT_id = Column(Integer, ForeignKey('EVTT.obj_id'))
    EVTT = relationship("EVTT", backref=backref('DAT', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    SNET_id = Column(Integer, ForeignKey('SNET.obj_id'))
    SNET = relationship("SNET", backref=backref('DAT', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    UIRADR_id = Column(Integer, ForeignKey('UIRADR.obj_id'))
    UIRADR = relationship("UIRADR", backref=backref('DAT', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.EVTT = get_attribute(root_xml, EVTT)
        self.SNET = get_attribute(root_xml, SNET)
        self.UIRADR = get_attribute(root_xml, UIRADR)

class EVTT(Base) :
    """Obsahuje informace o katalogu událostí Alert-C"""
    __tablename__ = 'EVTT'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    version = Column(Text)
    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.version = get_attribute(root_xml, "version")
        self.language = get_attribute(root_xml, "language") 

class SNET(Base) :
    """Informace o datové sadě sítě komunikací, na kterou jsou lokalizovány dopravní události"""
    __tablename__ = 'SNET'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    type = Column(Text)
    version = Column(Text)
    country = Column(Text)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.type = get_attribute(root_xml, "type")
        self.version = get_attribute(root_xml, "version")
        self.country = get_attribute(root_xml, "country") 

class UIRADR(Base) :
    """Informace o datové sadě UIADR"""
    __tablename__ = 'UIRADR'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    structure = Column(Text)
    version = Column(Text)
    date = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.structure = get_attribute(root_xml, "structure")
        self.version = get_attribute(root_xml, "version")
        self.date = get_attribute(root_xml, "date")

class MJD(Base) :
    """Zapouzdřuje veškeré informace o dopravních informacích."""
    __tablename__ = 'MJD'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    count = Column(Text)

    MSG = relationship("MSG", cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.count = get_attribute(root_xml, "count")

        self.MSG = get_attribute(root_xml, MSG, repeatable=True)

class MSG(Base) :
    """TAG zapouzdřující jednu zprávu v dokumentu"""
    __tablename__ = 'MSG'
    obj_id = Column(Integer, primary_key=True)

    MJD_id = Column(Integer, ForeignKey('MJD.obj_id'))

    value = Column(Text)

    id = Column(Text)
    version = Column(Text)
    type = Column(Text)
    planned = Column(Text)

    MTIME_id = Column(Integer, ForeignKey('MTIME.obj_id'))
    MTIME = relationship("MTIME", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    MTXT_id = Column(Integer, ForeignKey('MTXT.obj_id'))
    MTXT = relationship("MTXT", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    MEVT_id = Column(Integer, ForeignKey('MEVT.obj_id'))
    MEVT = relationship("MEVT", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    WDEST_id = Column(Integer, ForeignKey('WDEST.obj_id'))
    WDEST = relationship("WDEST", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    MLOC_id = Column(Integer, ForeignKey('MLOC.obj_id'))
    MLOC = relationship("MLOC", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    MDST_id = Column(Integer, ForeignKey('MDST.obj_id'))
    MDST = relationship("MDST", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    DIVLOC_id = Column(Integer, ForeignKey('DIVLOC.obj_id'))
    DIVLOC = relationship("DIVLOC", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    Location_id = Column(Integer, ForeignKey('Location.obj_id'))
    Location = relationship("Location", backref=backref('MSG', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.id = get_attribute(root_xml, "id")
        self.version = get_attribute(root_xml, "version")
        self.type = get_attribute(root_xml, "type")
        self.planned = get_attribute(root_xml, "planned") 

        self.MTIME = get_attribute(root_xml, MTIME)
        self.MTXT = get_attribute(root_xml, MTXT)
        self.MEVT = get_attribute(root_xml, MEVT)
        self.WDEST = get_attribute(root_xml, WDEST)
        self.MLOC = get_attribute(root_xml, MLOC)
        self.MDST = get_attribute(root_xml, MDST)
        self.DIVLOC = get_attribute(root_xml, DIVLOC)

    def set_Location(self, Location):
        self.Location = Location

    def get_coord_object(self):
        if self.MLOC:
            if self.MLOC.SNTL :
                if self.MLOC.SNTL.COORD :
                    return self.MLOC.SNTL.COORD

        if self.WDEST :
            if self.WDEST.COORD :
                return self.WDEST.COORD

        return None

    def get_coordinations(self):
        if self.MLOC:
            if self.MLOC.SNTL :
                if self.MLOC.SNTL.COORD :
                    return {
                        "coordsystem" : self.MLOC.SNTL.coordsystem,
                        "x" : self.MLOC.SNTL.COORD.x,
                        "y" : self.MLOC.SNTL.COORD.y
                    }

        if self.WDEST :
            if self.WDEST.COORD :
                return {
                    "coordsystem" : self.WDEST.coordsystem,
                    "x" : self.WDEST.COORD.x,
                    "y" : self.WDEST.COORD.y
                }

        return None

    def get_towncode(self):
        if self.MDST:
            if self.MDST.DEST:
                codes = [dest.TownCode for dest in self.MDST.DEST]
                return codes

        return None

    def get_regioncode(self):
        if self.MDST:
            if self.MDST.DEST:
                codes = [dest.RegionCode for dest in self.MDST.DEST]
                return codes

        return None

msg_location_id_index = Index('MSG_location_id_index', MSG.Location_id)

class MTIME(Base) :
    """Tag zapouzdřující časové informace o zprávě"""
    __tablename__ = 'MTIME'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    format = Column(Text)

    TGEN_id = Column(Integer, ForeignKey('TGEN.obj_id'))
    TGEN = relationship("TGEN", backref=backref('MTIME', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    TSTA_id = Column(Integer, ForeignKey('TSTA.obj_id'))
    TSTA = relationship("TSTA", backref=backref('MTIME', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    TSTO_id = Column(Integer, ForeignKey('TSTO.obj_id'))
    TSTO = relationship("TSTO", backref=backref('MTIME', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.format = get_attribute(root_xml, "format")
        
        self.TGEN = get_attribute(root_xml, TGEN)
        self.TSTA = get_attribute(root_xml, TSTA)
        self.TSTO = get_attribute(root_xml, TSTO)

class TGEN(Base) :
    """čas kdy byla zpráva vygenerována"""
    __tablename__ = 'TGEN'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

class TSTA(Base) :
    """čas od kdy zpráva platí nebo bude platná"""
    __tablename__ = 'TSTA'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

class TSTO(Base) :
    """čas do kdy bude zpráva platná"""
    __tablename__ = 'TSTO'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

class MTXT(Base) :
    """Kompletní textový popis události vyjadřující KDE, CO, KDY, případně JAK dlouho."""
    __tablename__ = 'MTXT'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.language = get_attribute(root_xml, "language") 

class MEVT(Base) :
    """zapouzdřuje veškeré informace o události"""
    __tablename__ = 'MEVT'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    TMCE_id = Column(Integer, ForeignKey('TMCE.obj_id'))
    TMCE = relationship("TMCE", backref=backref('MEVT', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    WCOND_id = Column(Integer, ForeignKey('WCOND.obj_id'))
    WCOND = relationship("WCOND", backref=backref('MEVT', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    MTNCOND_id = Column(Integer, ForeignKey('MTNCOND.obj_id'))
    MTNCOND = relationship("MTNCOND", backref=backref('MEVT', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    OTXT_id = Column(Integer, ForeignKey('OTXT.obj_id'))
    OTXT = relationship("OTXT", backref=backref('MEVT', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.TMCE = get_attribute(root_xml, TMCE)
        self.WCOND = get_attribute(root_xml, WCOND)
        self.MTNCOND = get_attribute(root_xml, MTNCOND)
        self.OTXT = get_attribute(root_xml, OTXT)

class TMCE(Base) :
    """zapouzdřuje veškeré TMC informace o události, atributy jsou vázány na normu 14819-1"""
    __tablename__ = 'TMCE'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    urgencyvalue = Column(Text)
    directionalityvalue = Column(Text)
    timescalevalue = Column(Text)
    durationtext = Column(Text)
    diversion = Column(Text)

    EVI = relationship("EVI", cascade="all, delete-orphan", single_parent=True)

    SPI_id = Column(Integer, ForeignKey('SPI.obj_id'))
    SPI = relationship("SPI", backref=backref('TMCE', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    DIV_id = Column(Integer, ForeignKey('DIV.obj_id'))
    DIV = relationship("DIV", backref=backref('TMCE', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    TXTMCE_id = Column(Integer, ForeignKey('TXTMCE.obj_id'))
    TXTMCE = relationship("TXTMCE", backref=backref('TMCE', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.urgencyvalue = get_attribute(root_xml, "urgencyvalue")
        self.directionalityvalue = get_attribute(root_xml, "directionalityvalue")
        self.timescalevalue = get_attribute(root_xml, "timescalevalue")
        self.durationtext = get_attribute(root_xml, "durationtext")
        self.diversion = get_attribute(root_xml, "diversion") 

        self.EVI = get_attribute(root_xml, EVI, repeatable=True) 
        self.SPI = get_attribute(root_xml, SPI)
        self.DIV = get_attribute(root_xml, DIV)
        self.TXTMCE = get_attribute(root_xml, TXTMCE)

class EVI(Base) :
    """Tag zapouzdřující informace o čísle události v katalogu událostí o jeho aktualizační třídě,
    kvantifikátoru, pořadí (pokud je zpráv více za sebou) včetně textového popisu aktualizační třídy a události.
    """
    __tablename__ = 'EVI'
    obj_id = Column(Integer, primary_key=True)

    TMCE_id = Column(Integer, ForeignKey('TMCE.obj_id'))

    value = Column(Text)

    eventcode = Column(Text)
    updateclass = Column(Text)
    quantifier = Column(Text)
    eventorder = Column(Text)

    TXUCL_id = Column(Integer, ForeignKey('TXUCL.obj_id'))
    TXUCL = relationship("TXUCL", backref=backref('EVI', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    TXEVC_id = Column(Integer, ForeignKey('TXEVC.obj_id'))
    TXEVC = relationship("TXEVC", backref=backref('EVI', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)



    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.eventcode = get_attribute(root_xml, "eventcode")
        self.updateclass = get_attribute(root_xml, "updateclass")
        self.quantifier = get_attribute(root_xml, "quantifier")
        self.eventorder = get_attribute(root_xml, "eventorder")
        
        self.TXUCL = get_attribute(root_xml, TXUCL)
        self.TXEVC = get_attribute(root_xml, TXEVC)


tmce_index = Index('TMCE_index', EVI.TMCE_id)

class TXUCL(Base) :
    """textový popis skupiny události podle ALERT-C"""
    __tablename__ = 'TXUCL'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.language = get_attribute(root_xml, "language") 

class TXEVC(Base) :
    """textový popis kódu události podle ALERT-C"""
    __tablename__ = 'TXEVC'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.language = get_attribute(root_xml, "language") 

class SPI(Base) :
    """informace o čísle doplňkové události, rychlostním limitu a délce ovlivněného úseku komunikace"""
    __tablename__ = 'SPI'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    supinfocode = Column(Text)
    supinfotext = Column(Text)
    speedlimit = Column(Text)
    length = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.supinfocode = get_attribute(root_xml, "supinfocode")
        self.supinfotext = get_attribute(root_xml, "supinfotext")
        self.speedlimit = get_attribute(root_xml, "speedlimit")
        self.length = get_attribute(root_xml, "length") 

class DIV(Base) :
    """TAG zapouzdřující informace o objížďce dle ALERT-C"""
    __tablename__ = 'DIV'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    diversioncode = Column(Text)
    diversiontext = Column(Text)
    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.diversioncode = get_attribute(root_xml, "diversioncode")
        self.diversiontext = get_attribute(root_xml, "diversiontext")
        self.language = get_attribute(root_xml, "language") 

class TXTMCE(Base) :
    """Text zprávy složený z hodnot jednotlivých událostí z ALERT-C katalogu událostí"""
    __tablename__ = 'TXTMCE'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.language = get_attribute(root_xml, "language") 

class WCOND(Base) :
    """zapouzdřuje informace o povětrnostních podmínkách týkajících se události typu „zimní zpravodajství“"""
    __tablename__ = 'WCOND'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    urgency = Column(Text)

    TEMP_id = Column(Integer, ForeignKey('TEMP.obj_id'))
    TEMP = relationship("TEMP", backref=backref('WCOND', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    CLD_id = Column(Integer, ForeignKey('CLD.obj_id'))
    CLD = relationship("CLD", backref=backref('WCOND', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    PREC_id = Column(Integer, ForeignKey('PREC.obj_id'))
    PREC = relationship("PREC", backref=backref('WCOND', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    WIND_id = Column(Integer, ForeignKey('WIND.obj_id'))
    WIND = relationship("WIND", backref=backref('WCOND', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    VIS_id = Column(Integer, ForeignKey('VIS.obj_id'))
    VIS = relationship("VIS", backref=backref('WCOND', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    WTXT_id = Column(Integer, ForeignKey('WTXT.obj_id'))
    WTXT = relationship("WTXT", backref=backref('WCOND', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    TTXT_id = Column(Integer, ForeignKey('TTXT.obj_id'))
    TTXT = relationship("TTXT", backref=backref('WCOND', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.urgency = get_attribute(root_xml, "urgency")
        
        self.TEMP = get_attribute(root_xml, TEMP)
        self.CLD = get_attribute(root_xml, CLD)
        self.PREC = get_attribute(root_xml, PREC)
        self.WIND = get_attribute(root_xml, WIND)
        self.VIS = get_attribute(root_xml, VIS)
        self.WTXT = get_attribute(root_xml, WTXT)
        self.TTXT = get_attribute(root_xml, TTXT)

class TEMP(Base) :
    """informace o teplotě definovanou rozsahem od-do ve zpravodajské oblasti"""
    __tablename__ = 'TEMP'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    unit = Column(Text)
    from_t = Column(Text)
    to_t = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.unit = get_attribute(root_xml, "unit")
        self.from_t = get_attribute(root_xml, "from_t")
        self.to_t = get_attribute(root_xml, "to_t") 

class CLD(Base) :
    """informace o oblačnosti ve zpravodajské oblasti"""
    __tablename__ = 'CLD'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    CloudyCode = Column(Text)
    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.CloudyCode = get_attribute(root_xml, "CloudyCode")
        self.language = get_attribute(root_xml, "language") 

class PREC(Base) :
    """informace o srážkách ve zpravodajské oblasti"""
    __tablename__ = 'PREC'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    PrecipitationCode = Column(Text)
    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.PrecipitationCode = get_attribute(root_xml, "PrecipitationCode")
        self.language = get_attribute(root_xml, "language") 

class WIND(Base) :
    """informace o síle a směru větru ve zpravodajské oblasti"""
    __tablename__ = 'WIND'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    WindCode = Column(Text)
    WindDirectionCode = Column(Text)
    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.WindCode = get_attribute(root_xml, "WindCode")
        self.WindDirectionCode = get_attribute(root_xml, "WindDirectionCode")
        self.language = get_attribute(root_xml, "language") 

class VIS(Base) :
    """informace o viditelnosti ve zpravodajské oblasti"""
    __tablename__ = 'VIS'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    VisibilityCode = Column(Text)
    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.VisibilityCode = get_attribute(root_xml, "VisibilityCode")
        self.language = get_attribute(root_xml, "language") 

class WTXT(Base) :
    """agregovaná textová informace o povětrnostních podmínkách ve zpravodajské oblasti"""
    __tablename__ = 'WTXT'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.language = get_attribute(root_xml, "language") 

class TTXT(Base) :
    """agregovaná textová informace o teplotních podmínkách ve zpravodajské oblasti"""
    __tablename__ = 'TTXT'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.language = get_attribute(root_xml, "language") 

class MTNCOND(Base) :
    """zapouzdřuje informace o sjízdnosti a stavu povrchu u sledovaných částí silniční sítě (třídy komunikace, část komunikace apod.)"""
    __tablename__ = 'MTNCOND'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    ISTN = relationship("ISTN", cascade="all, delete-orphan", single_parent=True)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.ISTN = get_attribute(root_xml, ISTN, repeatable=True)

class ISTN(Base) :
    """zapouzdřuje informace o sjízdnosti a stavu povrchu u sledovaných částí silniční sítě (třídy komunikace, část komunikace apod.)"""
    __tablename__ = 'ISTN'
    obj_id = Column(Integer, primary_key=True)

    MTNCOND_id = Column(Integer, ForeignKey('MTNCOND.obj_id'))

    value = Column(Text)

    InterestsSectionCode = Column(Text)
    InterestsSectionName = Column(Text)
    urgency = Column(Text)

    RCOND_id = Column(Integer, ForeignKey('RCOND.obj_id'))
    RCOND = relationship("RCOND", backref=backref('ISTN', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    RSCOND_id = Column(Integer, ForeignKey('RSCOND.obj_id'))
    RSCOND = relationship("RSCOND", backref=backref('ISTN', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    TXISTN_id = Column(Integer, ForeignKey('TXISTN.obj_id'))
    TXISTN = relationship("TXISTN", backref=backref('ISTN', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        
        self.InterestsSectionCode = get_attribute(root_xml, "InterestsSectionCode")
        self.InterestsSectionName = get_attribute(root_xml, "InterestsSectionName")
        self.urgency = get_attribute(root_xml, "urgency")
        
        self.RCOND = get_attribute(root_xml, RCOND)
        self.RSCOND = get_attribute(root_xml, RSCOND)
        self.TXISTN = get_attribute(root_xml, TXISTN)

class RCOND(Base) :
    """informace o sjízdnosti"""
    __tablename__ = 'RCOND'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    RoadConditionCode = Column(Text)
    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.RoadConditionCode = get_attribute(root_xml, "RoadConditionCode")
        self.language = get_attribute(root_xml, "language") 

class RSCOND(Base) :
    """informace o stavu povrchu vozovky"""
    __tablename__ = 'RSCOND'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    RoadSurfaceConditionCode = Column(Text)
    language = Column(Text)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.RoadSurfaceConditionCode = get_attribute(root_xml, "RoadSurfaceConditionCode")
        self.language = get_attribute(root_xml, "language") 

class TXISTN(Base) :
    """agregovaná textová informace o sjízdnosti stavu povrchu vozovky"""
    __tablename__ = 'TXISTN'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    language = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.language = get_attribute(root_xml, "language") 

class WDEST(Base) :
    """zapouzdřuje informace o místu a názvu zpravodajské oblasti"""
    __tablename__ = 'WDEST'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    coordsystem = Column(Text)
    NewsRegionCode = Column(Text)
    NewsRegionName = Column(Text)

    COORD_id = Column(Integer, ForeignKey('COORD.obj_id'))
    COORD = relationship("COORD", backref=backref('WDEST', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.coordsystem = get_attribute(root_xml, "coordsystem")
        self.NewsRegionCode = get_attribute(root_xml, "NewsRegionCode")
        self.NewsRegionName = get_attribute(root_xml, "NewsRegionName")
        
        self.COORD = get_attribute(root_xml, COORD)

class OTXT(Base) :
    """Volný text zadaný operátorem"""
    __tablename__ = 'OTXT'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

class MLOC(Base) :
    """TAG zapouzdřující informace o místu události"""
    __tablename__ = 'MLOC'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    TXPL_id = Column(Integer, ForeignKey('TXPL.obj_id'))
    TXPL = relationship("TXPL", backref=backref('MLOC', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    TMCL_id = Column(Integer, ForeignKey('TMCL.obj_id'))
    TMCL = relationship("TMCL", backref=backref('MLOC', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    SNTL_id = Column(Integer, ForeignKey('SNTL.obj_id'))
    SNTL = relationship("SNTL", backref=backref('MLOC', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.TXPL = get_attribute(root_xml, TXPL)
        self.TMCL = get_attribute(root_xml, TMCL)
        self.SNTL = get_attribute(root_xml, SNTL)

class TXPL(Base) :
    """textová informace popisující místo události nebo trasu objížďky"""
    __tablename__ = 'TXPL'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

class TMCL(Base) :
    """TAG zapouzdřující informace o místu události zakódované pomocí lokalizační databáze"""
    __tablename__ = 'TMCL'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    Primarycode = Column(Text)
    Extent = Column(Text)
    Direction = Column(Text)
    Roadid = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.Primarycode = get_attribute(root_xml, "Primarycode")
        self.Extent = get_attribute(root_xml, "Extent")
        self.Direction = get_attribute(root_xml, "Direction")
        self.Roadid = get_attribute(root_xml, "Roadid") 

class SNTL(Base) :
    """informace o místu události zadané pomocí úseků použité sítě komunikací"""
    __tablename__ = 'SNTL'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    coordsystem = Column(Text)
    count = Column(Text)

    COORD_id = Column(Integer, ForeignKey('COORD.obj_id'))
    COORD = relationship("COORD", backref=backref('SNTL', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    STEL = relationship("STEL", cascade="all, delete-orphan", single_parent=True)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.coordsystem = get_attribute(root_xml, "coordsystem")
        self.count = get_attribute(root_xml, "count")
        
        self.COORD = get_attribute(root_xml, COORD)
        self.STEL = get_attribute(root_xml, STEL, repeatable=True)

class COORD(Base) :
    """souřadnice události nebo zpravodajské oblasti v souřadnicovém systému
        definovaném v DOC\MJD\MSG\MLOC\SNTL – atribut „coordsystem“"""
    __tablename__ = 'COORD'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    x = Column(Text)
    y = Column(Text)

    Location_id = Column(Integer, ForeignKey('Location.obj_id'))
    Location = relationship("Location", backref=backref('COORD', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)
    
    def __init__(self, root_xml, Location=None):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.x = get_attribute(root_xml, "x")
        self.y = get_attribute(root_xml, "y")

        self.Location = Location

    def set_Location(self, Location):
        self.Location = Location

    def get_coordinations(self, db_session):
        coord_encapsulation = db_session.query(SNTL).filter(SNTL.COORD == self).first()
        if not coord_encapsulation:
            coord_encapsulation = db_session.query(WDEST).filter(WDEST.COORD == self).first()

        if not coord_encapsulation:
            raise Exception("There is not coord encapsulation!")

        return {
            "coordsystem" : coord_encapsulation.coordsystem,
            "x" : self.x,
            "y" : self.y
        }

    def get_doc_filename(self, db_session):
        wdest_obj = db_session.query(WDEST).filter(WDEST.COORD == self).first()
        if wdest_obj:
            msg_obj = db_session.query(MSG).filter(MSG.WDEST == wdest_obj).first()
        else:
            sntl_obj = db_session.query(SNTL).filter(SNTL.COORD == self).first()

            if not sntl_obj:
                return ""
            mloc_obj = db_session.query(MLOC).filter(MLOC.SNTL == sntl_obj).first()

            if not mloc_obj:
                return ""
            msg_obj = db_session.query(MSG).filter(MSG.MLOC == mloc_obj).first()

        if not msg_obj:
            return ""
        mjd_obj = db_session.query(MJD).filter(MJD.MSG.contains(msg_obj)).first()

        if not mjd_obj:
            return ""
        doc_obj = db_session.query(DOC).filter(DOC.MJD == mjd_obj).first()

        return doc_obj.file_name


coord_location_id_index = Index('COORD_location_id_index', COORD.Location_id)

class STEL(Base) :
    """Seznam čísel ovlivněných úseku"""
    __tablename__ = 'STEL'
    obj_id = Column(Integer, primary_key=True)

    SNTL_id = Column(Integer, ForeignKey('SNTL.obj_id'))

    value = Column(Text)

    el_code = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.el_code = get_attribute(root_xml, "el_code")

class MDST(Base) :
    """Tag zapouzdřující informace o místa události v souladu s republikovým číselníkem UIRADR"""
    __tablename__ = 'MDST'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    DEST = relationship("DEST", cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.DEST = get_attribute(root_xml, DEST, repeatable=True)

class DEST(Base) :
    """Informace o názvu a kódu administrativních jednotek"""
    __tablename__ = 'DEST'
    obj_id = Column(Integer, primary_key=True)

    MDST_id = Column(Integer, ForeignKey('MDST.obj_id'))

    value = Column(Text)

    CountryName = Column(Text)
    TownDistrictName = Column(Text)
    TownDistrictCode = Column(Text)
    TownName = Column(Text)
    TownCode = Column(Text)
    TownShip = Column(Text)
    TownShipCode = Column(Text)
    RegionName = Column(Text)
    RegionCode = Column(Text)

    STRE_id = Column(Integer, ForeignKey('STRE.obj_id'))
    STRE = relationship("STRE", backref=backref('DEST', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    ROAD_id = Column(Integer, ForeignKey('ROAD.obj_id'))
    ROAD = relationship("ROAD", backref=backref('DEST', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.CountryName = get_attribute(root_xml, "CountryName")
        self.TownDistrictName = get_attribute(root_xml, "TownDistrictName")
        self.TownDistrictCode = get_attribute(root_xml, "TownDistrictCode")
        self.TownName = get_attribute(root_xml, "TownName")
        self.TownCode = get_attribute(root_xml, "TownCode")
        self.TownShip = get_attribute(root_xml, "TownShip")
        self.TownShipCode = get_attribute(root_xml, "TownShipCode")
        self.RegionName = get_attribute(root_xml, "RegionName")
        self.RegionCode = get_attribute(root_xml, "RegionCode")
        
        self.STRE = get_attribute(root_xml, STRE)
        self.ROAD = get_attribute(root_xml, ROAD)

class STRE(Base) :
    """Informace o administrativní jednotce ulice"""
    __tablename__ = 'STRE'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    StreetName = Column(Text)
    StreetCode = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.StreetName = get_attribute(root_xml, "StreetName")
        self.StreetCode = get_attribute(root_xml, "StreetCode")

class ROAD(Base) :
    """Informace o komunikaci vzhledem k UIRADR"""
    __tablename__ = 'ROAD'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    RoadNumber = Column(Text)
    RoadClass = Column(Text)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.RoadNumber = get_attribute(root_xml, "RoadNumber")
        self.RoadClass = get_attribute(root_xml, "RoadClass") 

class DIVLOC(Base) :
    """TAG zapouzdřující informace o trase objížďky"""
    __tablename__ = 'DIVLOC'
    obj_id = Column(Integer, primary_key=True)

    value = Column(Text)

    DIVROUTE = relationship("DIVROUTE", cascade="all, delete-orphan", single_parent=True)

    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text

        self.DIVROUTE = get_attribute(root_xml, DIVROUTE, repeatable=True)

class DIVROUTE(Base) :
    """TAG zapouzdřující lokalizaci a detailní informace o trase objížďky"""
    __tablename__ = 'DIVROUTE'
    obj_id = Column(Integer, primary_key=True)

    DIVLOC_id = Column(Integer, ForeignKey('DIVLOC.obj_id'))

    value = Column(Text)

    description = Column(Text)

    TXPL_id = Column(Integer, ForeignKey('TXPL.obj_id'))
    TXPL = relationship("TXPL", backref=backref('DIVROUTE', order_by=obj_id), cascade="all, delete-orphan", single_parent=True)
    
    def __init__(self, root_xml):
        if root_xml == None :
            return

        self.value = root_xml.text
        
        self.description = get_attribute(root_xml, "description")
        
        self.TXPL = get_attribute(root_xml, TXPL)





