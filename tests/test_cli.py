from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from slackbot.__main__ import main, resolve_channel, resolve_token
from slackbot.config import (
    SlackbotConfig,
    home_config_path,
    load_config,
    load_merged_config,
    repo_config_path,
)
from slackbot.slack_api import SlackClient, SlackMessageRequest, SlackMessageResponse


class ResolveTokenTests(unittest.TestCase):
    def test_resolve_token_uses_local_config(self) -> None:
        config = SlackbotConfig(bot_user_oauth_token="xoxb-test")
        self.assertEqual(resolve_token(None, config, dry_run=False), "xoxb-test")

    def test_resolve_token_allows_dry_run_without_env(self) -> None:
        self.assertEqual(
            resolve_token(None, SlackbotConfig(), dry_run=True),
            "dry-run-token",
        )


class ResolveChannelTests(unittest.TestCase):
    def test_resolve_channel_uses_default_channel(self) -> None:
        config = SlackbotConfig(default_channel="#general")
        self.assertEqual(resolve_channel(None, config), "#general")


class ConfigTests(unittest.TestCase):
    def test_merged_config_uses_home_token_and_repo_channel(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            repo_file = tmpdir_path / ".slackbot.json"
            home_file = tmpdir_path / "home-config.json"
            repo_file.write_text(
                json.dumps(
                    {
                        "bot_user_oauth_token": "xoxb-legacy-repo",
                        "default_channel": "#repo",
                    }
                ),
                encoding="utf-8",
            )
            home_file.write_text(
                json.dumps(
                    {
                        "bot_user_oauth_token": "xoxb-home",
                        "default_channel": "#home",
                    }
                ),
                encoding="utf-8",
            )

            config = load_merged_config(repo_path=repo_file, home_path=home_file)

        self.assertEqual(config.bot_user_oauth_token, "xoxb-home")
        self.assertEqual(config.default_channel, "#repo")

    def test_merged_config_ignores_repo_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            repo_file = tmpdir_path / ".slackbot.json"
            home_file = tmpdir_path / "home-config.json"
            repo_file.write_text(
                json.dumps(
                    {
                        "bot_user_oauth_token": "xoxb-repo-only",
                        "default_channel": "#repo",
                    }
                ),
                encoding="utf-8",
            )

            config = load_merged_config(repo_path=repo_file, home_path=home_file)

        self.assertIsNone(config.bot_user_oauth_token)
        self.assertEqual(config.default_channel, "#repo")


class DryRunTests(unittest.TestCase):
    def test_slack_client_dry_run_returns_payload(self) -> None:
        client = SlackClient("xoxb-test")
        response = client.post_message(
            SlackMessageRequest(channel="C123", text="Hello"), dry_run=True
        )

        self.assertEqual(response.channel, "C123")
        self.assertEqual(response.ts, "dry-run")
        self.assertTrue(response.raw["ok"])
        self.assertEqual(response.raw["payload"]["text"], "Hello")

    def test_main_dry_run_prints_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["--channel", "C123", "--message", "Hello", "--dry-run"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["payload"]["channel"], "C123")


class SetupTests(unittest.TestCase):
    def test_first_run_prompts_and_saves_home_token_and_repo_channel(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home_file = Path(tmpdir) / ".slackbot" / "config.json"
            repo_file = Path(tmpdir) / ".slackbot.json"
            stdout = io.StringIO()
            response = SlackMessageResponse(
                channel="#general",
                ts="123.456",
                raw={"ok": True, "channel": "#general", "ts": "123.456"},
            )

            with redirect_stdout(stdout):
                with mock.patch("slackbot.__main__.home_config_path", return_value=home_file):
                    with mock.patch("slackbot.__main__.repo_config_path", return_value=repo_file):
                        with mock.patch("slackbot.__main__.has_interactive_terminal", return_value=True):
                            with mock.patch("slackbot.__main__.getpass.getpass", return_value="xoxb-secret"):
                                with mock.patch("builtins.input", return_value="#general"):
                                    with mock.patch(
                                        "slackbot.__main__.SlackClient.post_message",
                                        return_value=response,
                                    ):
                                        exit_code = main(["--message", "Hello"])

            self.assertEqual(exit_code, 0)
            saved_home_config = load_config(home_file)
            saved_repo_config = load_config(repo_file)
            self.assertEqual(saved_home_config.bot_user_oauth_token, "xoxb-secret")
            self.assertIsNone(saved_home_config.default_channel)
            self.assertIsNone(saved_repo_config.bot_user_oauth_token)
            self.assertEqual(saved_repo_config.default_channel, "#general")
            self.assertIn(f"Saved Slack token to {home_file}", stdout.getvalue())
            self.assertIn(f"Saved default channel to {repo_file}", stdout.getvalue())

    def test_load_config_ignores_legacy_bot_token_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".slackbot.json"
            config_file.write_text(
                json.dumps({"bot_token": "xoxb-legacy", "default_channel": "#general"}),
                encoding="utf-8",
            )

            config = load_config(config_file)

        self.assertIsNone(config.bot_user_oauth_token)
        self.assertEqual(config.default_channel, "#general")

    def test_setup_only_saves_config_without_sending_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home_file = Path(tmpdir) / ".slackbot" / "config.json"
            repo_file = Path(tmpdir) / ".slackbot.json"

            with mock.patch("slackbot.__main__.home_config_path", return_value=home_file):
                with mock.patch("slackbot.__main__.repo_config_path", return_value=repo_file):
                    with mock.patch("slackbot.__main__.has_interactive_terminal", return_value=True):
                        with mock.patch("slackbot.__main__.getpass.getpass", return_value="xoxb-secret"):
                            with mock.patch("builtins.input", return_value="#general"):
                                with mock.patch("slackbot.__main__.SlackClient.post_message") as post_message:
                                    exit_code = main(["--setup"])

            self.assertEqual(exit_code, 0)
            post_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
