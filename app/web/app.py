from aiohttp.web import (
    Application as AiohttpApplication,
    Request as AiohttpRequest,
    View as AiohttpView,
)
from aiohttp_apispec import setup_aiohttp_apispec
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from app.admin.models import AdminModel
from app.store.store import Store
from app.web.config import Config
from app.web.middlewares import setup_middlewares

__all__ = ("Application",)


class Application(AiohttpApplication):
    def __init__(self, config: Config, store: Store) -> None:
        super().__init__()
        self.config = config
        self.store = store


class Request(AiohttpRequest):
    admin: AdminModel | None = None

    @property
    def app(self) -> Application:
        return super().app


class View(AiohttpView):
    @property
    def request(self) -> Request:
        return super().request

    @property
    def store(self) -> Store:
        return self.request.app.store

    @property
    def data(self) -> dict:
        return self.request.get("data", {})


def setup_app(config: Config) -> Application:
    from app.web.routes import setup_routes  # noqa: PLC0415

    store = Store(config)
    app = Application(config, store)
    setup_routes(app)
    session_setup(app, EncryptedCookieStorage(store.config.aiohttp_session.key))
    setup_middlewares(app)
    setup_aiohttp_apispec(
        app, title="Admin panel tg game", url="/docs/json", swagger_path="/docs"
    )
    app.on_startup.append(store.database.connect)
    app.on_startup.append(store.admin_accessor.connect)
    app.on_cleanup.append(store.admin_accessor.disconnect)
    app.on_cleanup.append(store.database.disconnect)

    return app
