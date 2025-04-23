import typing

from app.game.views import QuestionAddView, QuestionDeleteView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application") -> None:
    app.router.add_view("/game/add_question", QuestionAddView)
    app.router.add_view("/game/delete_question", QuestionDeleteView)
