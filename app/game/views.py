import logging

from aiohttp.web import Response
from aiohttp.web_exceptions import HTTPConflict
from aiohttp_apispec import docs, request_schema, response_schema

from app.game.schemes import QuestionIdSchema, QuestionSchema
from app.web.app import View
from app.web.auth import auth_required
from app.web.exceptions import QuestionCreateError
from app.web.utils import json_response

logger = logging.getLogger(__name__)


class QuestionAddView(View):
    @docs(tags=["game"], summary="Add question")
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    @auth_required
    async def post(self) -> Response:
        try:
            question = await self.store.game_accessor.create_question(
                question=self.data["question"],
                answer=self.data["answer"],
            )
        except QuestionCreateError as e:
            logger.error(e)
            raise HTTPConflict from e
        return json_response(data=QuestionSchema().dump(question))


class QuestionDeleteView(View):
    @docs(tags=["game"], summary="Add question")
    @request_schema(QuestionIdSchema)
    @auth_required
    async def post(self) -> Response:
        await self.store.game_accessor.delete_question_by_id(
            self.data["question_id"]
        )
        return json_response()
