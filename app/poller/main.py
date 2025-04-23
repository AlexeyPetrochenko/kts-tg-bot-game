import asyncio
import logging

from app.poller.poller import setup_poller
from app.web.config import get_config_path, load_config
from app.web.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
NUMBER_OF_QUEUES = 2


async def main() -> None:
    config = load_config(get_config_path())
    poller = setup_poller(config, NUMBER_OF_QUEUES)
    try:
        await poller.start()
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(e)
    finally:
        logger.info("Poller stopped")
        await poller.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
