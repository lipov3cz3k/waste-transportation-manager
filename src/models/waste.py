from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, Boolean
from sqlalchemy.orm import relationship, backref
from database import Base
from models.location import Address



class Cheb(Base) :
    __tablename__ = 'Cheb'
    obj_id = Column(Integer, primary_key=True)

    internal_key = Column(Text)
    container_type = Column(Text)
    interval = Column(Text)
    waste_type = Column(Text)
    waste_code = Column(Integer)
    waste_name = Column(Text)
    tech_grp = Column(Text)
    quantity = Column(Integer)
    quantity_unit = Column(Text)
    start = Column(Text)
    end = Column(Text)
    state = Column(Boolean)
    invoicing = Column(Boolean)
    in_route = Column(Boolean)

    #address
    address_id = Column(Integer, ForeignKey('Address.id'))
    address = relationship("Address")

    name = Column(Text)
    dispatcher_note = Column(Text)
    invoice_note = Column(Text)
    note = Column(Text)
    days = Column(Text)
    fix_note = Column(Text)
    row = Column(Integer)
    order = Column(Integer)

    def __init__(self, session, data):
        if data == None :
            return
        self.internal_key = '{}-{}'.format(data['waste_type'], data['row'])

        self.container_type = data['container_type']
        self.interval = data['interval']
        self.waste_type = data['waste_type']
        self.waste_code = data['waste_code']
        self.waste_name = data['waste_name']
        self.tech_grp = data['tech_grp']
        self.quantity = data['quantity']
        self.quantity_unit = data['quantity_unit']
        self.start = data['start']
        self.end = data['end']
        self.state = data['state'] in ['T']
        self.invoicing = data['invoicing']
        self.in_route = data['in_route'] in ['T']
        self.address = Address.as_unique(session, 
                                         city=str(data['city']),
                                         street=str(data['street']),
                                         house_number=str(data['house_number'])
                                         )

        self.name = data['name']
        self.dispatcher_note = data['dispatcher_note']
        self.invoice_note = data['invoice_note']
        self.note = data['note']
        self.days = data['days']
        self.fix_note = data['fix_note']
        self.row = data['row']
        self.order = data['order']


    def __repr__(self):
        return '%s %s %r' % (self.obj_id, self.internal_key, self.waste_type)

        
