from aiohttp.web import (
    Application as AiohttpApplication,
)

from app.store.store import Store
from app.web.config import Config
from app.web.routes import setup_routes

__all__ = ("Application",)


class Application(AiohttpApplication):
    config: Config | None = None
    store: Store | None = None
    database: None = None


app = Application()


def setup_app(config_path: str) -> Application:
    setup_routes(app)
    return app
