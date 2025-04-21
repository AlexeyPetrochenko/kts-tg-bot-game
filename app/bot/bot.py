from app.bot.poller import Poller
from app.store.store import Store
from app.web.config import Config


class Bot:
    def __init__(self, store: Store) -> None:
        self.store = store
        self.poller = Poller(store)

    async def run_bot(self) -> None:
        await self.store.tg_api.connect()
        await self.store.database.connect()
        self.poller.start()

    async def stop_bot(self) -> None:
        await self.poller.stop()
        await self.store.database.disconnect()
        await self.store.tg_api.disconnect()


def setup_bot(config: Config) -> Bot:
    store = Store(config)
    return Bot(store)
