from inspect import isclass
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, Boolean, String, Float
from sqlalchemy.orm import relationship, backref
from database import Base, UniqueMixin
from models.location import Address
from hashlib import sha1

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
    interval = Column(Float)
    days_odd = Column(Integer)
    days_even = Column(Integer)
    days_orig = Column(Text)
    note = Column(Text)
    details = Column(Text)
    variant = Column(Text)

    __mapper_args__ = {
        'polymorphic_on':type,
        'polymorphic_identity':'Container',
        'with_polymorphic':'*'
    }

    def __init__(self, **kwargs):
        data = kwargs['data']
        self.address = Address.as_unique(kwargs['db_session'], 
                                         city=str(data['city']),
                                         street=str(data['street']),
                                         house_number=str(data['house_number']),
                                         postal=int(data.get('postal')) if data.get('postal') else None, 
                                         country=str(data.get('country')) if data.get('country') else None, 
                                         latitude=float(data.get('latitude')) if data.get('latitude') else None, 
                                         longitude=float(data.get('longitude')) if data.get('longitude') else None
                                         )
        self.population = int(data.get('population')) if data.get('population') else None
        self.name = data['name']
        self.waste_type = data['waste_type']
        self.waste_code = data['waste_code']
        self.waste_name = data['waste_name']
        self.quantity = data['quantity']
        self.quantity_unit = data['quantity_unit']
        try:
            self.capacity = int(data.get('capacity')) if data.get('capacity') else None
        except ValueError:
            print("Can't  covert capacity %s to number" % data.get('capacity'))
        self.start = data['start']
        self.end = data['end']
        self.interval = data['interval']
        self.days_odd = data['days_odd']
        self.days_even = data['days_even']
        self.days_orig = data['days_orig']

        self.note = data['note']
        self.variant = data['variant']

    def __str__(self):
        return self.id

    def get_properties(self):
        return dict(id=self.id,
                    container_type=self.type,
                    waste_code=self.waste_code,
                    latitude=self.address.latitude,
                    longitude=self.address.longitude,
                    quantity=self.quantity,
                    capacity=self.capacity,
                    interval=self.interval)

class Cheb(UniqueMixin, Container) :
    __tablename__ = 'Cheb'
    id = Column(Integer, ForeignKey('Container.id'), primary_key=True)
    internal_key = Column(Text)
    hash = Column(Integer, unique=True, nullable=False)
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

    def __init__(self, **kwargs):
        data = kwargs['data']
        if data == None :
            return
        super().__init__(**kwargs)
        self.internal_key = '{}-{}'.format(data['waste_type'], data['row'])
        s = sha1()
        s.update(data['tech_grp'].encode('utf-8'))
        s.update(data['city'].encode('utf-8'))
        s.update(data['street'].encode('utf-8'))
        s.update(data['house_number'].encode('utf-8'))
        s.update(str(data['row']).encode('utf-8'))
        s.update(data['start'].date().isoformat().encode('utf-8'))
        self.hash = s.hexdigest()
        self.tech_grp = data['tech_grp']
        self.state = data['state'] in ['T']
        self.invoicing = data['invoicing']
        self.in_route = data['in_route'] in ['T']
        self.dispatcher_note = data['dispatcher_note']
        self.invoice_note = data['invoice_note']
        self.fix_note = data['fix_note']
        self.row = data['row']
        self.order = data['order']

    @classmethod
    def unique_hash(cls, **kwargs):
        data = kwargs['data']
        s = sha1()
        s.update(data['tech_grp'].encode('utf-8'))
        s.update(data['city'].encode('utf-8'))
        s.update(data['street'].encode('utf-8'))
        s.update(data['house_number'].encode('utf-8'))
        s.update(str(data['row']).encode('utf-8'))
        s.update(data['start'].date().isoformat().encode('utf-8'))
        return s.hexdigest()

    @classmethod
    def unique_filter(cls, query, **kwargs):
        data = kwargs['data']
        s = sha1()
        s.update(data['tech_grp'].encode('utf-8'))
        s.update(data['city'].encode('utf-8'))
        s.update(data['street'].encode('utf-8'))
        s.update(data['house_number'].encode('utf-8'))
        s.update(str(data['row']).encode('utf-8'))
        s.update(data['start'].date().isoformat().encode('utf-8'))
        return query.filter(Cheb.hash == s.hexdigest())

    def __repr__(self):
        return '%s %s %r' % (self.id, self.internal_key, self.waste_type)
cheb_hash_index = Index('Cheb_hash_index', Cheb.hash)

class Jihlava(UniqueMixin, Container) :
    __tablename__ = 'Jihlava'
    id = Column(Integer, ForeignKey('Container.id'), primary_key=True)
    object_id = Column(Integer, unique=True)
    ownership = Column(Text)
    optimum = Column(Integer)
    coefficient = Column(Integer)
    ratio = Column(Integer)
    __mapper_args__ = {'polymorphic_identity':'Jihlava'}

    def __init__(self, **kwargs):
        data = kwargs['data']
        if data == None :
            return
        super().__init__(**kwargs)

        self.object_id = data.get('object_id')
        self.ownership = data.get('ownership')
        self.optimum = data.get('optimum')
        self.coefficient = data.get('coefficient')
        self.ratio = data.get('ratio')

    @classmethod
    def unique_hash(cls, **kwargs):
        return kwargs['data']['object_id']

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(Jihlava.object_id == kwargs['data']['object_id'])

jihlava_object_id_index = Index('Jihlava_object_id_index', Jihlava.object_id)

class Stavanger(UniqueMixin, Container) :
    __tablename__ = 'Stavanger'
    id = Column(Integer, ForeignKey('Container.id'), primary_key=True)
    object_id = Column(Integer, unique=True)
    counter = Column(Integer)
    fillheight = Column(Integer)
    date = Column(Text)
    __mapper_args__ = {'polymorphic_identity':'Stavanger'}

    def __init__(self, **kwargs):
        data = kwargs['data']
        if data == None :
            return
        super().__init__(**kwargs)
        self.object_id = data.get('object_id')
        self.counter = data.get('counter')
        self.fillheight = data.get('fillheight')
        self.date = data.get('date')

    @classmethod
    def unique_hash(cls, **kwargs):
        return kwargs['data']['object_id']

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(Stavanger.object_id == kwargs['data']['object_id'])
stavanger_object_id_index = Index('Stavanger_object_id_index', Stavanger.object_id)

class Plzen(UniqueMixin, Container) :
    __tablename__ = 'Plzen'
    id = Column(Integer, ForeignKey('Container.id'), primary_key=True)
    object_id = Column(Integer)
    hash = Column(Integer, unique=True, nullable=False)

    __mapper_args__ = {'polymorphic_identity':'Plzen'}

    def __init__(self, **kwargs):
        data = kwargs['data']
        if data == None :
            return
        super().__init__(**kwargs)

        self.object_id = data.get('object_id')
        self.hash = "%s%s" % (data.get('object_id'), data.get('variant'))

    @classmethod
    def unique_hash(cls, **kwargs):
        return "%s%s" % (kwargs['data']['object_id'], kwargs['data']['variant'])

    @classmethod
    def unique_filter(cls, query, **kwargs):
        return query.filter(Plzen.object_id == "%s%s" % (kwargs['data']['object_id'], kwargs['data']['variant']))

Plzen_object_id_index = Index('Plzen_object_id_index', Plzen.object_id)
