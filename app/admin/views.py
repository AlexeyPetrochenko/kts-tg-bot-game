from aiohttp.web_exceptions import HTTPConflict, HTTPForbidden
from aiohttp.web_response import Response
from aiohttp_apispec import docs, request_schema, response_schema
from aiohttp_session import get_session, new_session

from app.admin.schemes import AdminSchema
from app.web.app import View
from app.web.auth import auth_required
from app.web.exceptions import AdminCreateError
from app.web.utils import json_response, verify_password


class AdminLoginView(View):
    @docs(tags=["admin"], summary="Login admin")
    @request_schema(AdminSchema)
    @response_schema(AdminSchema(only=("id", "email")), 200)
    async def post(self) -> Response:
        credentials = self.data
        try:
            admin = await self.store.admin_accessor.get_by_email(
                credentials["email"]
            )
        except AdminCreateError as e:
            raise HTTPConflict from e
        if admin is None:
            raise HTTPForbidden
        if not verify_password(credentials["password"], admin.password):
            raise HTTPForbidden

        session = await new_session(self.request)
        session["user_email"] = credentials["email"]

        return json_response(data=AdminSchema().dump(admin))


class AdminCurrentView(View):
    @docs(tags=["admin"], summary="Get current admin")
    @response_schema(AdminSchema(only=("id", "email")), 200)
    @auth_required
    async def get(self) -> Response:
        return json_response(data=AdminSchema().dump(self.request.admin))


class AdminLogoutView(View):
    @docs(tags=["admin"], summary="Logout admin")
    @response_schema(AdminSchema(only=("id", "email")), 200)
    @auth_required
    async def get(self) -> Response:
        session = await get_session(self.request)
        session.invalidate()
        return json_response(data=AdminSchema().dump(self.request.admin))
