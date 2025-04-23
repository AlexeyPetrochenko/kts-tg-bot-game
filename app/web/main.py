from aiohttp.web import run_app

from app.web.app import setup_app
from app.web.config import get_config_path, load_config
from app.web.logger import setup_logging

if __name__ == "__main__":
    setup_logging()
    config = load_config(get_config_path())
    run_app(setup_app(config))
