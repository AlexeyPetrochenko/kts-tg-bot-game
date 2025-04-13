from app.web.config import Config


class Store:
    def __init__(self, config: Config) -> None:
        from app.store.bot.manager import BotManager
        from app.store.database.database import Database
        from app.store.tg_api.accessor import TGApiAccessor

        self.config = config
        self.bot_manager = BotManager(self)
        self.database = Database(self)
        self.tg_api = TGApiAccessor(self)
