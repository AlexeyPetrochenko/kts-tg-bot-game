from app.web.config import Config


class Store:
    def __init__(self, config: Config) -> None:
        from app.store.bot.manager import setup_bot_manager
        from app.store.database.database import Database
        from app.store.game.accessor import GameAccessor
        from app.store.game.fsm_manager import FsmManager
        from app.store.tg_api.accessor import TGApiAccessor

        self.config = config
        self.bot_manager = setup_bot_manager(self)
        self.database = Database(self)
        self.game_accessor = GameAccessor(self)
        self.fsm_manager = FsmManager(self)
        self.tg_api = TGApiAccessor(self)
