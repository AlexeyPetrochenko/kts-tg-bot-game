import logging
import threading
from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar
from wsgiref.simple_server import WSGIServer

from prometheus_client import Gauge, start_http_server

if TYPE_CHECKING:
    from app.store.game.fsm_manager import FsmManager
    from app.store.store import Store

logger = logging.getLogger(__name__)
T = TypeVar("T", bound="FsmManager")


class MetricsBot:
    def __init__(self, store: "Store") -> None:
        self.store = store
        self.port = store.config.metrics.port
        self.server: WSGIServer | None = None
        self.t: threading.Thread | None = None
        self.ACTIVE_GAMES = Gauge("app_active_games", "Количество активных игр")
        self.ACTIVE_PLAYERS = Gauge(
            "app_active_players", "Количество активных игроков"
        )

    def start_metrics_server(self) -> None:
        try:
            self.server, self.t = start_http_server(self.port, addr="0.0.0.0")
            logger.info("Metrics server started successfully")
        except Exception as e:
            logger.error("Failed to start metrics server: %s", e)

    def stop_metrics_server(self) -> None:
        self.server.shutdown()
        self.t.join()


def increment_active_games(func: Callable) -> Callable:
    @wraps(func)
    def inner(self: T, *args: Any, **kwargs: Any) -> Any:
        if self.store.bot_metrics.server:
            self.store.bot_metrics.ACTIVE_GAMES.inc()
        return func(self, *args, **kwargs)

    return inner


def decrement_active_games(func: Callable) -> Callable:
    @wraps(func)
    def inner(self: T, *args: Any, **kwargs: Any) -> Any:
        if self.store.bot_metrics.server:
            self.store.bot_metrics.ACTIVE_GAMES.dec()
        return func(self, *args, **kwargs)

    return inner


def increment_active_players(func: Callable) -> Callable:
    @wraps(func)
    def inner(self: T, *args: Any, **kwargs: Any) -> Any:
        if self.store.bot_metrics.server:
            self.store.bot_metrics.ACTIVE_PLAYERS.inc()
        return func(self, *args, **kwargs)

    return inner


def decrement_active_players(func: Callable) -> Callable:
    @wraps(func)
    def inner(self: T, *args: Any, **kwargs: Any) -> Any:
        if self.store.bot_metrics.server:
            self.store.bot_metrics.ACTIVE_PLAYERS.dec()
        return func(self, *args, **kwargs)

    return inner
