import logging
from dataclasses import dataclass

import yaml
from marshmallow.exceptions import ValidationError
from marshmallow_dataclass import class_schema

from app.web.exceptions import LoadConfigError

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    token: str


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"

    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class Config:
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None


ConfigSchema = class_schema(Config)()


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    try:
        config = ConfigSchema.load(raw_config)
    except ValidationError as e:
        logger.error("Error validating config file: %s", e)
        raise LoadConfigError("Error validating config file") from e
    return config
