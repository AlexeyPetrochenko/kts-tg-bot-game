import logging
import os
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
class AdminConfig:
    email: str
    password: str


@dataclass
class SessionConfig:
    key: str


@dataclass
class RabbitMQConfig:
    host: str = "localhost"
    port: int = 5672
    user: str = "guest"
    password: str = "guest"

    @property
    def RABBIT_MQ_URL(self) -> str:  # noqa: N802
        return f"pyamqp://{self.user}:{self.password}@{self.host}:{self.port}/"


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
    admin: AdminConfig | None = None
    bot: BotConfig | None = None
    database: DatabaseConfig | None = None
    aiohttp_session: SessionConfig | None = None
    broker: RabbitMQConfig | None = None


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


def get_config_path() -> str:
    if os.getenv("ENV") == "dev":
        return os.path.join(
            os.path.dirname(__file__), "..", "..", "local", "etc", "config.yaml"
        )
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "etc", "config.yaml"
    )
