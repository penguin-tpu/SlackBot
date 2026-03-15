from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from slackbot.__main__ import main, resolve_channel, resolve_token
from slackbot.config import SlackbotConfig, load_config
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
    def test_first_run_prompts_and_saves_local_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".slackbot.json"
            stdout = io.StringIO()
            response = SlackMessageResponse(
                channel="#general",
                ts="123.456",
                raw={"ok": True, "channel": "#general", "ts": "123.456"},
            )

            with redirect_stdout(stdout):
                with mock.patch("slackbot.__main__.config_path", return_value=config_file):
                    with mock.patch("slackbot.__main__.has_interactive_terminal", return_value=True):
                        with mock.patch("slackbot.__main__.getpass.getpass", return_value="xoxb-secret"):
                            with mock.patch("builtins.input", return_value="#general"):
                                with mock.patch(
                                    "slackbot.__main__.SlackClient.post_message",
                                    return_value=response,
                                ):
                                    exit_code = main(["--message", "Hello"])

            self.assertEqual(exit_code, 0)
            saved_config = load_config(config_file)
            self.assertEqual(saved_config.bot_user_oauth_token, "xoxb-secret")
            self.assertEqual(saved_config.default_channel, "#general")
            self.assertIn("Saved Slack config", stdout.getvalue())

    def test_load_config_accepts_legacy_bot_token_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".slackbot.json"
            config_file.write_text(
                json.dumps({"bot_token": "xoxb-legacy", "default_channel": "#general"}),
                encoding="utf-8",
            )

            config = load_config(config_file)

        self.assertEqual(config.bot_user_oauth_token, "xoxb-legacy")

    def test_setup_only_saves_config_without_sending_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".slackbot.json"

            with mock.patch("slackbot.__main__.config_path", return_value=config_file):
                with mock.patch("slackbot.__main__.has_interactive_terminal", return_value=True):
                    with mock.patch("slackbot.__main__.getpass.getpass", return_value="xoxb-secret"):
                        with mock.patch("builtins.input", return_value="#general"):
                            with mock.patch("slackbot.__main__.SlackClient.post_message") as post_message:
                                exit_code = main(["--setup"])

            self.assertEqual(exit_code, 0)
            post_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
