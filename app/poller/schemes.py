from pydantic import BaseModel


class Message(BaseModel):
    chat_id: int
    text: str
    message_id: int
    from_id: int
    from_username: str


class CallbackQuery(BaseModel):
    callback_id: str
    chat_id: int
    command: str
    message_id: int
    from_id: int
    from_username: str


class Update(BaseModel):
    update_id: int
    date: int
    body: Message | CallbackQuery
