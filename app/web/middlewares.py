import typing

from aiohttp import web
from aiohttp.abc import Request
from aiohttp.web import Response


@web.middleware
async def example_mw(request: Request, handler: typing.Callable) -> Response:
    return await handler(request)
