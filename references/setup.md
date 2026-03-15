# SlackBot Setup

## Credential to use

For posting messages with `chat.postMessage`, use the Slack `Bot User OAuth Token`.
It usually starts with `xoxb-`.

Do not use:

- `App ID`
- `Client ID`
- `Client Secret`
- `Signing Secret`
- `Verification Token`

Those are for app identity, OAuth flows, or inbound request verification, not for
posting a Slack message with this tool.

## Required Slack app scopes

- `chat:write`
- `chat:write.public` only if posting to public channels without inviting the bot first

## First-run setup

Run:

```bash
python3 scripts/send_message.py --setup
```

The tool stores the Bot User OAuth Token and optional default channel in
different places:

- Bot User OAuth Token: `~/.slackbot/config.json`
- Optional per-repo default channel: `.slackbot.json`

The repo-local file is gitignored.

## Finding the channel value

You can use either:

- a channel ID like `C01234567`
- a channel name like `#general`

Channel ID is preferred because it is more stable.

One easy way to find the channel ID is from the Slack web URL:

```text
https://app.slack.com/client/TXXXXXXX/CXXXXXXX
```

The `CXXXXXXX` segment is the channel ID.
