from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from typing import Sequence

from .config import (
    SlackbotConfig,
    SlackbotConfigError,
    config_path,
    load_config,
    save_config,
)
from .slack_api import SlackApiError, SlackClient, SlackMessageRequest


DEFAULT_MESSAGE = "Hello from slackbot!"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a message to Slack using a Bot User OAuth Token.",
    )
    parser.add_argument(
        "--channel",
        help="Slack channel ID or name, for example C12345678 or #general. Channel ID is preferred.",
    )
    parser.add_argument(
        "--message",
        default=DEFAULT_MESSAGE,
        help=f"Message text to send. Defaults to: {DEFAULT_MESSAGE!r}",
    )
    parser.add_argument(
        "--thread-ts",
        help="Optional thread timestamp to reply inside an existing thread.",
    )
    parser.add_argument(
        "--token",
        help="Temporary Bot User OAuth Token override for this run (usually starts with xoxb-).",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Prompt for local Slack settings and save them in the repo directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the message payload flow without calling Slack.",
    )

    parser.usage = """python -m slackbot [-h] [--channel CHANNEL] [--message MESSAGE] [--thread-ts THREAD_TS] [--token TOKEN] [--setup] [--dry-run]
examples: python -m slackbot --channel C01234567 --message "Hello from the CLI"
          python -m slackbot --setup
          python -m slackbot --channel C01234567 --message "Hello from the CLI" --thread-ts 12345.6789
          python -m slackbot --channel C01234567 --dry-run
"""
    return parser


def has_interactive_terminal() -> bool:
    return sys.stdin.isatty()


def prompt_for_local_config(existing: SlackbotConfig) -> SlackbotConfig:
    print("Slackbot first-run setup")
    print("The Bot User OAuth Token and optional default channel will be stored locally in this repo.")

    bot_user_oauth_token = _prompt_secret(
        "Bot User OAuth Token (xoxb-...)",
        current_value=existing.bot_user_oauth_token,
    )
    default_channel = _prompt_text(
        "Default Slack channel ID or name (optional, channel ID preferred)",
        current_value=existing.default_channel,
    )
    return SlackbotConfig(
        bot_user_oauth_token=bot_user_oauth_token,
        default_channel=default_channel,
    )


def resolve_local_config(args: argparse.Namespace) -> SlackbotConfig:
    path = config_path()
    try:
        config = load_config(path)
    except SlackbotConfigError as exc:
        raise SlackApiError(str(exc)) from exc

    should_prompt_for_setup = args.setup or (
        not args.dry_run and (not path.exists() or not config.bot_user_oauth_token)
    )
    if not should_prompt_for_setup:
        return config

    if not has_interactive_terminal():
        raise SlackApiError(
            "Slack config is missing and no interactive terminal is available. "
            "Run with --setup in a terminal."
        )

    seeded_config = SlackbotConfig(
        bot_user_oauth_token=(
            args.token
            or os.environ.get("SLACK_BOT_TOKEN")
            or config.bot_user_oauth_token
        ),
        default_channel=args.channel or config.default_channel,
    )
    saved_config = prompt_for_local_config(seeded_config)
    save_config(saved_config, path)
    print(f"Saved Slack config to {path}")
    return saved_config


def resolve_token(
    explicit_token: str | None,
    config: SlackbotConfig,
    *,
    dry_run: bool,
) -> str:
    token = (
        explicit_token
        or os.environ.get("SLACK_BOT_TOKEN")
        or config.bot_user_oauth_token
    )
    if token:
        return token
    if dry_run:
        return "dry-run-token"
    raise SlackApiError(
        "Missing Bot User OAuth Token. Run with --setup, set SLACK_BOT_TOKEN, or pass --token."
    )


def resolve_channel(explicit_channel: str | None, config: SlackbotConfig) -> str:
    channel = explicit_channel or config.default_channel
    if channel:
        return channel
    raise SlackApiError(
        "Missing Slack channel. Pass --channel or configure a default channel with --setup."
    )


def _prompt_secret(prompt: str, *, current_value: str | None) -> str:
    while True:
        suffix = " [press Enter to keep current]" if current_value else ""
        value = getpass.getpass(f"{prompt}{suffix}: ").strip()
        if value:
            return value
        if current_value:
            return current_value
        print("A value is required.")


def _prompt_text(prompt: str, *, current_value: str | None) -> str | None:
    suffix = f" [{current_value}]" if current_value else ""
    value = input(f"{prompt}{suffix}: ").strip()
    if value:
        return value
    return current_value


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = resolve_local_config(args)
        if args.setup:
            return 0
        token = resolve_token(args.token, config, dry_run=args.dry_run)
        channel = resolve_channel(args.channel, config)
        client = SlackClient(token)
        request = SlackMessageRequest(
            channel=channel,
            text=args.message,
            thread_ts=args.thread_ts,
        )
        response = client.post_message(request, dry_run=args.dry_run)
    except SlackApiError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")

    if args.dry_run:
        print(json.dumps(response.raw, indent=2, sort_keys=True))
    else:
        print(f"Sent message to {response.channel} at ts={response.ts}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
