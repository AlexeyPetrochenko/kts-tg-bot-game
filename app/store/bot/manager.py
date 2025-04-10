import typing

from app.bot.schemes import Update

if typing.TYPE_CHECKING:
    from app.store.store import Store


class BotManager:
    def __init__(self, store: "Store"):
        self.store = store
        self.bot = None

    async def handle_updates(self, updates: Update) -> None:
        await self.store.tg_api.send_message(updates.message)
