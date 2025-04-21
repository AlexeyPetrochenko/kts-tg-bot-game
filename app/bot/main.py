import asyncio
import logging

from app.bot.bot import setup_bot
from app.web.config import get_config_path, load_config
from app.web.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def main() -> None:
    config = load_config(get_config_path())
    bot = setup_bot(config)
    try:
        await bot.run_bot()
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Bot stopped")
        await bot.stop_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logger.info(e)
