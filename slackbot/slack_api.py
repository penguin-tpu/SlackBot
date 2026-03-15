from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


SLACK_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


class SlackApiError(RuntimeError):
    """Raised when Slack returns an API or transport error."""


@dataclass(frozen=True)
class SlackMessageRequest:
    channel: str
    text: str
    thread_ts: str | None = None

    def as_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "channel": self.channel,
            "text": self.text,
        }
        if self.thread_ts:
            payload["thread_ts"] = self.thread_ts
        return payload


@dataclass(frozen=True)
class SlackMessageResponse:
    channel: str
    ts: str
    raw: dict[str, Any]


class SlackClient:
    def __init__(self, bot_user_oauth_token: str, timeout_seconds: float = 10.0) -> None:
        self._bot_user_oauth_token = bot_user_oauth_token
        self._timeout_seconds = timeout_seconds

    def post_message(
        self,
        message: SlackMessageRequest,
        *,
        dry_run: bool = False,
    ) -> SlackMessageResponse:
        payload = message.as_payload()
        if dry_run:
            return SlackMessageResponse(
                channel=message.channel,
                ts="dry-run",
                raw={"ok": True, "dry_run": True, "payload": payload},
            )

        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            SLACK_POST_MESSAGE_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self._bot_user_oauth_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )

        try:
            with request.urlopen(http_request, timeout=self._timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise SlackApiError(
                f"Slack returned HTTP {exc.code}: {details}"
            ) from exc
        except error.URLError as exc:
            raise SlackApiError(f"Could not reach Slack API: {exc.reason}") from exc

        data = json.loads(response_body)
        if not data.get("ok"):
            error_code = data.get("error", "unknown_error")
            raise SlackApiError(f"Slack API rejected the message: {error_code}")

        return SlackMessageResponse(
            channel=str(data["channel"]),
            ts=str(data["ts"]),
            raw=data,
        )
