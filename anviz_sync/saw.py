"""
    nobix.lib.saw
    ~~~~~~~~~~~~~

    SQLAalchemy wrapper based on http://github.com/lucuma/sqlalchemy-wrapper
    code.
"""
import threading

import sqlalchemy
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData
from sqlalchemy import orm
from sqlalchemy.orm.exc import UnmappedClassError

def _create_scoped_session(db, query_cls):
    session = orm.sessionmaker(autoflush=True, autocommit=False,
                               query_cls=query_cls)
    return orm.scoped_session(session)

def _tablemaker(db):
    def make_sa_table(*args, **kwargs):
        if len(args) > 1 and isinstance(args[1], db.Column):
            args = (args[0], db.metadata) + args[1:]
        return sqlalchemy.Table(*args, **kwargs)

    return make_sa_table

def _include_sqlalchemy(db):
    for module in sqlalchemy, sqlalchemy.orm:
        for key in module.__all__:
            if not hasattr(db, key):
                setattr(db, key, getattr(module, key))
    db.Table = _tablemaker(db)
    db.event = sqlalchemy.event


class BaseQuery(orm.Query):

    def get_or_error(self, uid, error):
        """Like :meth:`get` but raises an error if not found instead of
        returning `None`.
        """
        rv = self.get(uid)
        if rv is None:
            if isinstance(error, Exception):
                raise error
            return error()
        return rv

    def first_or_error(self, error):
        """Like :meth:`first` but raises an error if not found instead of
        returning `None`.
        """
        rv = self.first()
        if rv is None:
            if isinstance(error, Exception):
                raise error
            return error()
        return rv

    def paginate(self, **kwargs):
        """Paginate this results.
        Returns a :class:`Pagination` object.
        """
        return Pagination(self, **kwargs)


class _QueryProperty(object):

    def __init__(self, db):
        self.db = db

    def __get__(self, obj, type):
        try:
            mapper = orm.class_mapper(type)
            if mapper:
                return type.query_class(mapper, session=self.db.session())
        except UnmappedClassError:
            return None


class EngineConnector(object):

    def __init__(self, sa_obj):
        self._sa_obj = sa_obj
        self._engine = None
        self._connected_for = None
        self._lock = threading.Lock()

    def get_engine(self):
        with self._lock:
            uri = self._sa_obj.uri
            info = self._sa_obj.info
            options = self._sa_obj.options
            echo = options.get('echo')
            if (uri, echo) == self._connected_for:
                return self._engine
            self._engine = engine = sqlalchemy.create_engine(info, **options)
            self._connected_for = (uri, echo)
            return engine


class Model(object):
    """Baseclass for custom user models.
    """

    #: the query class used.  The :attr:`query` attribute is an instance of
    #: this class. By default a :class:`BaseQuery` is used.
    query_class = BaseQuery

    #: an instance of :attr:`query_class`.  Can be used to query the database
    #: for instance of this model.
    query = None

    def __iter__(self):
        """Returns an iterable that supports .next() so we can
        do dict(sa_instance).
        """
        for k in self.__dict__.keys():
            if not k.startswith('_'):
                yield (k, getattr(self, k))

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


class SQLAlchemy(object):
    """This class is used to instantiate a SQLAlchemy connection to a database.
    """

    def __init__(self, query_cls=BaseQuery):
        self.uri = None
        self.info = None
        self.options = None
        self.connector = None
        self._engine_lock = threading.Lock()
        self.session = _create_scoped_session(self, query_cls=query_cls)

        self.Model = self.make_declarative_base()

        _include_sqlalchemy(self)

    def make_declarative_base(self):
        """Creates the declatative base."""
        base = declarative_base(cls=Model, name='Model')
        base.db = self
        base.query = _QueryProperty(self)
        return base

    def _cleanup_options(self, **kwargs):
        options = dict([
            (key, val)
            for key, val in kwargs.items()
            if val is not None
        ])
        return self._apply_driver_hacks(options)

    def _apply_driver_hacks(self, options):
        if self.info.drivername == 'mysql':
            self.info.query.setdefault('charset', 'utf8')
            options.setdefault('pool_size', 10)
            options.setdefault('pool_recycle', 7200)

        elif self.info.drivername == 'sqlite':
            no_pool = options.get('poll_size') == 0
            memory_based = self.info.database in (None, '', ':memory:')
            if memory_based and no_pool:
                raise ValueError(
                    "SQLite in-memory database with an empty queue"
                    " (pool_size = 0) is not posibe due to data loss."
                )
        return options

    def configure(self, uri='sqlite://', app=None, echo=False, pool_size=None,
                  pool_timeout=None, pool_recycle=None, convert_unicode=True):
        self.uri = uri
        self.info = make_url(uri)
        self.options = self._cleanup_options(
            echo = echo,
            pool_size = pool_size,
            pool_timeout = pool_timeout,
            pool_recycle = pool_recycle,
            convert_unicode = convert_unicode
        )
        self.session.configure(bind=self.engine)
        self.Model.metadata.bind = self.engine

    @property
    def engine(self):
        """Gives access to the engine."""
        if self.info is None:
            raise ValueError(
                "You must configure SQLAlchemy via .configure() method before"
                " working with any connection to database."
            )
        with self._engine_lock:
            connector = self.connector
            if connector is None:
                connector = EngineConnector(self)
                self.connector = connector
            return connector.get_engine()

    @property
    def metadata(self):
        """Proxy for Model.metadata"""
        return self.Model.metadata

    @property
    def query(self):
        """Proxy for session.query"""
        return self.session.query

    def add(self, *args, **kwargs):
        """Proxy for session.add"""
        return self.session.add(*args, **kwargs)

    def add_all(self, *args, **kwargs):
        """Proxy for session.add_all"""
        return self.session.add_all(*args, **kwargs)

    def flush(self, *args, **kwargs):
        """Proxy for session.flush"""
        return self.session.flush(*args, **kwargs)

    def commit(self):
        """Proxy for session.commit"""
        return self.session.commit()

    def rollback(self):
        """Proxy for session.rollback"""
        return self.session.rollback()

    def create_all(self):
        """Creates all tables."""
        self.Model.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """Drops all tables."""
        self.Model.metadata.drop_all(bind=self.engine)

    def reflect(self, meta=None):
        """Reflection tables from the database.
        """
        meta = meta or MetaData()
        meta.reflect(bind=self.bind)
        return meta

    def __repr__(self):
        return "<SQLAlchemy('{0}')>".format(
            self.uri if self.uri is not None else '<not-configured>'
        )
