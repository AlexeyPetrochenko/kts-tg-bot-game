import asyncio
import logging
import os

from app.store.store import Store
from app.web.config import load_config
from app.web.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "etc", "config.yaml"
    )
    config = load_config(config_path)
    store = Store(config)

    try:
        await store.tg_api.connect()
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Bot stopped")
        await store.tg_api.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logger.info(e)
