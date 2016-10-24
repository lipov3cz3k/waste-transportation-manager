from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, Boolean, String
from sqlalchemy.orm import relationship, backref
from database import Base
from models.location import Address

class Container(Base) : 
    __tablename__ = 'Container'
    id = Column(Integer, primary_key=True)
    type = Column(String(20))

    #address
    address_id = Column(Integer, ForeignKey('Address.id'))
    address = relationship("Address")
    population = Column(Integer)
    name = Column(Text)
    #container info
    container_type = Column(Text)
    waste_type = Column(Text)
    waste_code = Column(Integer)
    waste_name = Column(Text)
    capacity = Column(Integer)
    quantity = Column(Integer)
    quantity_unit = Column(Text)
    start = Column(Text)
    end = Column(Text)
    interval = Column(Text)
    days = Column(Text)
    note = Column(Text)
    details = Column(Text)

    __mapper_args__ = {
        'polymorphic_on':type,
        'polymorphic_identity':'Container',
        'with_polymorphic':'*'
    }

    def __init__(self, session, data):
        self.address = Address.as_unique(session, 
                                         city=str(data['city']),
                                         street=str(data['street']),
                                         house_number=str(data['house_number']), 
                                         longitude=float(data.get('latitude', -1)), 
                                         latitude=float(data.get('longitude', -1))
                                         )
        self.population = int(data.get('population', -1))
        self.name = data['name']
        self.waste_type = data['waste_type']
        self.waste_code = data['waste_code']
        self.waste_name = data['waste_name']
        self.quantity = data['quantity']
        self.quantity_unit = data['quantity_unit']
        try:
            self.capacity = int(data.get('capacity', -1))
        except ValueError:
            print("Can't  covert capacity %s to number" % data.get('capacity'))
            self.capacity = -1
        self.start = data['start']
        self.end = data['end']
        self.interval = data['interval']
        self.days = data['days']

        self.note = data['note']

class Cheb(Container) :
    __tablename__ = 'Cheb'
    id = Column(Integer, ForeignKey('Container.id'), primary_key=True)
    internal_key = Column(Text)
    tech_grp = Column(Text)
    state = Column(Boolean)
    invoicing = Column(Boolean)
    in_route = Column(Boolean)

    dispatcher_note = Column(Text)
    invoice_note = Column(Text)
    fix_note = Column(Text)
    row = Column(Integer)
    order = Column(Integer)
    __mapper_args__ = {'polymorphic_identity':'Cheb'}

    def __init__(self, session, data):
        if data == None :
            return
        super().__init__(session, data)
        self.internal_key = '{}-{}'.format(data['waste_type'], data['row'])
        self.tech_grp = data['tech_grp']
        self.state = data['state'] in ['T']
        self.invoicing = data['invoicing']
        self.in_route = data['in_route'] in ['T']
        self.dispatcher_note = data['dispatcher_note']
        self.invoice_note = data['invoice_note']
        self.fix_note = data['fix_note']
        self.row = data['row']
        self.order = data['order']

    def __repr__(self):
        return '%s %s %r' % (self.obj_id, self.internal_key, self.waste_type)
