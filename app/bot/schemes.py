from dataclasses import dataclass


@dataclass
class Message:
    message_id: int
    from_id: int
    from_name: str
    chat_id: int
    text: str
    date: str


@dataclass
class Update:
    update_id: int
    message: Message
