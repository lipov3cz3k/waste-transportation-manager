from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from common.config import local_config

engine_path = "sqlite:///%s" % local_config.path_db_file
#engine_path = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset=utf8'.format("root", "Admin.123", "localhost", 3306, "master_thesis2")
engine = create_engine(engine_path, convert_unicode=True)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import ddr.ddr_models
    Base.metadata.create_all(bind=engine)

    # recreate index of EVI - use only on DB where index doesn't exist
    #ddr.ddr_models.tmce_index.create(bind=engine)
    #ddr.ddr_models.msg_location_id_index.create(bind=engine)
    #ddr.ddr_models.location_osm_id_index.create(bind=engine)
    #ddr.ddr_models.coord_location_id_index.create(bind=engine)