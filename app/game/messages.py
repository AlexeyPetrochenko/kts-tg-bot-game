MESSAGES = {
    "not_enough_players": (
        "Недостаточно игроков ({count}/{min_players}).\nИгра завершена."
    ),
    "players_connected": ("Подключились ({count}/{min_players}) игроков"),
    "player_timeout": "Вы не успели, переход хода",
}


def get_message(key: str, **kwargs) -> str:  # type: ignore[no-untyped-def]
    try:
        return MESSAGES[key].format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Unknown message key: {key}") from e
    except IndexError as e:
        raise ValueError(
            f"Missing formatting argument for message '{key}': {e}"
        ) from e
