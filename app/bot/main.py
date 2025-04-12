import asyncio
import logging
import os

from app.bot.poller import Poller
from app.store.store import Store
from app.web.config import load_config
from app.web.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def config_path() -> str:
    if os.getenv("ENV") == "dev":
        return os.path.join(
            os.path.dirname(__file__), "..", "..", "local", "etc", "config.yaml"
        )
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "etc", "config.yaml"
    )


async def main() -> None:
    config = load_config(config_path())
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
