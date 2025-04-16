from marshmallow import Schema, fields
from marshmallow.validate import OneOf

from app.game.models import GameParticipantState, GameState


# TODO: Пока нигде не задействовал
class QuestionSchema(Schema):
    question_id = fields.Int(dump_only=True)
    question = fields.Str(required=True)
    answer = fields.Str(required=True)


class GameSchema(Schema):
    game_id = fields.Int(dump_only=True)
    chat_id = fields.Int(required=True)
    state = fields.Str(validate=OneOf(state.value for state in GameState))
    question_id = fields.Int()
    revealed_letter = fields.Str(default="")


class UserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    tg_user_id = fields.Int(required=True)
    username = fields.Str(required=True)
    first_name = fields.Str()
    last_name = fields.Str()


class GameParticipantSchema(Schema):
    participant_id = fields.Int(dump_only=True)
    game_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    state = fields.Str(
        validate=OneOf(state.value for state in GameParticipantState)
    )
    turn_order = fields.Int()
    points = fields.Int(default=0)
