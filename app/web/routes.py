from aiohttp.web_app import Application

__all__ = ("setup_routes",)


def setup_routes(application: Application) -> None:
    import app.users.routes

    app.users.routes.register_urls(application)
