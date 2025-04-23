from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from aiohttp.web import Response
from aiohttp.web_exceptions import HTTPForbidden, HTTPUnauthorized
from aiohttp_session import get_session

if TYPE_CHECKING:
    from app.web.app import View


T = TypeVar("T", bound="View")


def auth_required(handler: Callable) -> Callable:
    async def inner(self: T, *args: Any, **kwargs: Any) -> Response:
        session = await get_session(self.request)
        user_email = session.get("user_email")
        if user_email is None:
            raise HTTPUnauthorized
        user = await self.store.admin_accessor.get_by_email(user_email)
        if user is None:
            raise HTTPForbidden
        self.request.admin = user
        return await handler(self, *args, **kwargs)

    return inner
