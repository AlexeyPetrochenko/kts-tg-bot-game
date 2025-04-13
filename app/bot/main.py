import asyncio
import logging

from app.bot.poller import Poller
from app.store.store import Store
from app.web.config import get_config_path, load_config
from app.web.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config(get_config_path())
    store = Store(config)
    await store.tg_api.connect()
    poller = Poller(store)

    try:
        poller.start()
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Bot stopped")
        await poller.stop()
        await store.tg_api.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logger.info(e)
