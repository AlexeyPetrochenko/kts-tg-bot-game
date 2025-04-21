import typing

from app.admin.routers import setup_routes as admin_setup_routes
from app.game.routers import setup_routes as game_setup_routes

if typing.TYPE_CHECKING:
    from app.web.app import Application

__all__ = ("setup_routes",)


def setup_routes(application: "Application") -> None:
    admin_setup_routes(application)
    game_setup_routes(application)
