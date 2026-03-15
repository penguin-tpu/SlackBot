from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SlackbotConfigError(RuntimeError):
    """Raised when the local Slackbot config cannot be loaded."""


@dataclass(frozen=True)
class SlackbotConfig:
    bot_user_oauth_token: str | None = None
    default_channel: str | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_path() -> Path:
    return repo_root() / ".slackbot.json"


def load_config(path: Path | None = None) -> SlackbotConfig:
    resolved_path = path or config_path()
    if not resolved_path.exists():
        return SlackbotConfig()

    try:
        data = json.loads(resolved_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SlackbotConfigError(
            f"Config file {resolved_path} is not valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise SlackbotConfigError(
            f"Config file {resolved_path} must contain a JSON object."
        )

    return SlackbotConfig(
        bot_user_oauth_token=_optional_string(
            data.get("bot_user_oauth_token") or data.get("bot_token")
        ),
        default_channel=_optional_string(data.get("default_channel")),
    )


def save_config(config: SlackbotConfig, path: Path | None = None) -> Path:
    resolved_path = path or config_path()
    payload: dict[str, Any] = {
        "bot_user_oauth_token": config.bot_user_oauth_token,
        "default_channel": config.default_channel,
    }
    resolved_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return resolved_path


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
