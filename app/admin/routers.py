import typing

from app.admin.views import AdminCurrentView, AdminLoginView, AdminLogoutView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application") -> None:
    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
    app.router.add_view("/admin.logout", AdminLogoutView)
