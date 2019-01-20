import asyncio

from sqlalchemy.engine.url import URL

from gino.api import Gino as _Gino, GinoExecutor as _Executor
from gino.engine import GinoConnection as _Connection, GinoEngine as _Engine
from gino.strategies import GinoStrategy

from starlette.datastructures import CommaSeparatedStrings, DatabaseURL, Secret
from starlette.exceptions import HTTPException


class StarletteModelMixin:
    @classmethod
    async def get_or_404(cls, *args, **kwargs):
        rv = await cls.get(*args, **kwargs)
        if rv is None:
            raise HTTPException(404)
        return rv


class GinoExecutor(_Executor):
    async def first_or_404(self, *args, **kwargs):
        rv = await self.first(*args, **kwargs)
        if rv is None:
            raise HTTPException(404)
        return rv


class GinoConnection(_Connection):
    async def first_or_404(self, *args, **kwargs):
        rv = await self.first(*args, **kwargs)
        if rv is None:
            raise HTTPException(404)
        return rv


class GinoEngine(_Engine):
    connection_cls = GinoConnection

    async def first_or_404(self, *args, **kwargs):
        rv = await self.first(*args, **kwargs)
        if rv is None:
            raise HTTPException(404)
        return rv


class StarletteStrategy(GinoStrategy):
    name = 'starlette'
    engine_cls = GinoEngine


class Gino(_Gino):
    """Support Starlette web server.
    The common usage looks like this::
        from starlette.applications import Starlette
        from starlette.config import Config
        from .middleware.gino import Gino
        db = Gino()
        config = Config('.env')
        app = Starlette()
        db.init_app(app, config)
    By :meth:`init_app` GINO subscribes to a few events on scarlette, so that
    GINO could use database configuration provided in .env file or by environment
    variables to initialize the bound engine. The config includes:
    * ``driver`` - the database driver, default is ``asyncpg``.
    * ``host`` - database server host, default is ``localhost``.
    * ``port`` - database server port, default is ``5432``.
    * ``user`` - database server user, default is ``postgres``.
    * ``password`` - database server password, default is empty.
    * ``database`` - database name, default is ``postgres``.
    * ``dsn`` - a SQLAlchemy database URL to create the engine, its existence
      will replace all previous connect arguments.
    * ``pool_min_size`` - the initial number of connections of the db pool.
    * ``pool_max_size`` - the maximum number of connections in the db pool.
    * ``echo`` - enable SQLAlchemy echo mode.
    * ``ssl`` - SSL context passed to ``asyncpg.connect``, default is ``None``.
    """
    
    model_base_classes = _Gino.model_base_classes + (StarletteModelMixin,)
    query_executor = GinoExecutor
    
    def init_app(self, app, config):
        self.config = config
        app.add_event_handler('startup', self.startup)
        app.add_event_handler('shutdown', self.shutdown)
                                
    def __init__(self, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if app is not None:
            self.init_app(app)
            
    def __call__(self, scope):
        if scope['type'] == 'lifespan':
            return GinoLifespan(
                self.app, scope, startup=self.startup, shutdown=self.shutdown
            )
        return self.app(scope)
        
    async def startup(self):
        if self.config('dsn'):
            dsn = self.config('dsn')
        else:
            dsn = URL(
                drivername=self.config('driver', default='asyncpg'),
                host=self.config('host', default='localhost'),
                port=self.config('port', default=5432),
                username=self.config('user', default='postgres'),
                password=self.config('password', default=''),
                database=self.config('database', default='postgres'),
            )
        
        await self.set_bind(
            dsn,
            echo=self.config('echo', default=False),
            min_size=self.config('pool_min_size', default=5),
            max_size=self.config('pool_max_size', default=10),
            ssl=self.config('ssl', default=None),
            loop=asyncio.get_event_loop(),
        )
        
    async def shutdown(self):
        await self.pop_bind().close()