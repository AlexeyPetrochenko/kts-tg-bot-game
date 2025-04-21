from dataclasses import dataclass


@dataclass
class Message:
    chat_id: int
    text: str
    message_id: int
    from_id: int
    from_username: str


@dataclass
class CallbackQuery:
    callback_id: str
    chat_id: int
    command: str
    message_id: int
    from_id: int
    from_username: str


@dataclass
class Update:
    update_id: int
    date: int
    body: Message | CallbackQuery
