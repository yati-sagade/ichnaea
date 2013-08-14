from sqlalchemy import create_engine
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
    Unicode,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

_Model = declarative_base()


RADIO_TYPE = {
    '': -1,
    'gsm': 0,
    'cdma': 1,
    'umts': 2,
    'lte': 3,
}
RADIO_TYPE_KEYS = list(RADIO_TYPE.keys())

STAT_TYPE = {
    '': -1,
    'location': 0,
}
STAT_TYPE_INVERSE = dict((v, k) for k, v in STAT_TYPE.items())

# TODO add signal to list of reserved words
# reported upstream at http://www.sqlalchemy.org/trac/ticket/2791
from sqlalchemy.dialects.mysql import base
base.RESERVED_WORDS.add('signal')
del base


class Cell(_Model):
    __tablename__ = 'cell'
    __table_args__ = (
        Index('cell_idx', 'radio', 'mcc', 'mnc', 'lac', 'cid'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8',
        }
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # lat/lon * decimaljson.FACTOR
    lat = Column(Integer)
    lon = Column(Integer)
    # mapped via RADIO_TYPE
    radio = Column(SmallInteger)
    # int in the range 0-1000
    mcc = Column(SmallInteger)
    # int in the range 0-1000 for gsm
    # int in the range 0-32767 for cdma (system id)
    mnc = Column(Integer)
    lac = Column(Integer)
    cid = Column(Integer)
    psc = Column(Integer)
    range = Column(Integer)

cell_table = Cell.__table__


class CellMeasure(_Model):
    __tablename__ = 'cell_measure'
    __table_args__ = (
        Index('cell_measure_lat_idx', 'lat'),
        Index('cell_measure_lon_idx', 'lon'),
        Index('cell_measure_key_idx', 'radio', 'mcc', 'mnc', 'lac', 'cid'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8',
            'mysql_row_format': 'compressed',
            'mysql_key_block_size': '4',
        }
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # lat/lon * decimaljson.FACTOR
    lat = Column(Integer)
    lon = Column(Integer)
    time = Column(DateTime)
    accuracy = Column(Integer)
    altitude = Column(Integer)
    altitude_accuracy = Column(Integer)
    # mapped via RADIO_TYPE
    radio = Column(SmallInteger)
    mcc = Column(SmallInteger)
    mnc = Column(Integer)
    lac = Column(Integer)
    cid = Column(Integer)
    psc = Column(Integer)
    asu = Column(SmallInteger)
    signal = Column(SmallInteger)
    ta = Column(SmallInteger)

cell_measure_table = CellMeasure.__table__


class Wifi(_Model):
    __tablename__ = 'wifi'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8',
    }

    key = Column(String(40), primary_key=True)
    # lat/lon * decimaljson.FACTOR
    lat = Column(Integer)
    lon = Column(Integer)
    range = Column(Integer)

wifi_table = Wifi.__table__


class WifiMeasure(_Model):
    __tablename__ = 'wifi_measure'
    __table_args__ = (
        Index('wifi_measure_lat_idx', 'lat'),
        Index('wifi_measure_lon_idx', 'lon'),
        Index('wifi_measure_key_idx', 'key'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8',
            'mysql_row_format': 'compressed',
            'mysql_key_block_size': '4',
        }
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # lat/lon * decimaljson.FACTOR
    lat = Column(Integer)
    lon = Column(Integer)
    time = Column(DateTime)
    accuracy = Column(Integer)
    altitude = Column(Integer)
    altitude_accuracy = Column(Integer)
    key = Column(String(40))
    channel = Column(SmallInteger)
    signal = Column(SmallInteger)

wifi_measure_table = WifiMeasure.__table__


class Measure(_Model):
    __tablename__ = 'measure'
    __table_args__ = (
        Index('measure_time_idx', 'time'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8',
            'mysql_row_format': 'compressed',
            'mysql_key_block_size': '4',
        }
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # lat/lon * decimaljson.FACTOR
    lat = Column(Integer)
    lon = Column(Integer)
    time = Column(DateTime)
    accuracy = Column(Integer)
    altitude = Column(Integer)
    altitude_accuracy = Column(Integer)
    radio = Column(SmallInteger)  # mapped via RADIO_TYPE
    # json blobs
    cell = Column(LargeBinary)
    wifi = Column(LargeBinary)

measure_table = Measure.__table__


class Score(_Model):
    __tablename__ = 'score'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8',
    }

    id = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(Integer, index=True, unique=True)
    value = Column(Integer)

score_table = Score.__table__


class Stat(_Model):
    __tablename__ = 'stat'
    __table_args__ = (
        Index('stat_key_time_idx', 'key', 'time'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8',
        }
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # mapped via STAT_TYPE
    key = Column(SmallInteger, index=True)
    time = Column(Date)
    value = Column(BigInteger)

    @property
    def name(self):
        return STAT_TYPE_INVERSE.get(self.key, '')

    @name.setter
    def name(self, value):
        self.key = STAT_TYPE[value]


stat_table = Stat.__table__


class User(_Model):
    __tablename__ = 'user'
    __table_args__ = (
        Index('user_token_idx', 'token'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8',
        }
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(36))
    nickname = Column(Unicode(128))

user_table = User.__table__


# request.db_session and db_tween_factory are inspired by pyramid_tm
# to provide lazy session creation, session closure and automatic
# rollback in case of errors

def db_session(request):
    session = getattr(request, '_db_session', None)
    if session is None:
        request._db_session = session = request.registry.db_master.session()
    return session


def db_tween_factory(handler, registry):

    def db_tween(request):
        response = handler(request)
        session = getattr(request, '_db_session', None)
        if session is not None:
            # only deal with requests with a session
            if response.status.startswith(('4', '5')):  # pragma: no cover
                # never commit on error
                session.rollback()
            session.close()
        return response

    return db_tween


class Database(object):

    def __init__(self, uri, socket=None, create=True, echo=False,
                 isolation_level='REPEATABLE READ'):
        options = {
            'pool_recycle': 3600,
            'pool_size': 10,
            'pool_timeout': 10,
            'echo': echo,
            # READ COMMITTED
            'isolation_level': isolation_level,
        }
        options['connect_args'] = {'charset': 'utf8'}
        if socket:  # pragma: no cover
            options['connect_args'] = {'unix_socket': socket}
        options['execution_options'] = {'autocommit': False}
        self.engine = create_engine(uri, **options)
        self.session_factory = sessionmaker(
            bind=self.engine, autocommit=False, autoflush=False)

        # create tables
        if create:
            with self.engine.connect() as conn:
                trans = conn.begin()
                _Model.metadata.create_all(self.engine)
                trans.commit()

    def session(self):
        return self.session_factory()
