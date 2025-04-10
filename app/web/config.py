from dataclasses import dataclass

import yaml


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


def load_config(config_path: str) -> Config:
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    return Config(
        bot=BotConfig(token=raw_config["bot"]["token"]),
        database=DatabaseConfig(**raw_config["database"]),
    )
