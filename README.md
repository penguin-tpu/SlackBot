# slackbot

Small Python package for sending a message to Slack with a bot integration.

This repository also works as a Codex/OpenAI skill. The skill entrypoint is
[SKILL.md](/home/tk/Downloads/slackbot/SKILL.md), with setup details in
[references/setup.md](/home/tk/Downloads/slackbot/references/setup.md).

## Installation

Install from repo

```bash
pip install .
```

Set up a local development environment with `uv`

```bash
uv sync
```

## Usage

```bash
usage: python -m slackbot [-h] [--channel CHANNEL] [--message MESSAGE] [--thread-ts THREAD_TS] [--token TOKEN] [--setup] [--dry-run]
examples: python -m slackbot --channel C01234567 --message "Hello from the CLI"
          python -m slackbot --setup
          python -m slackbot --channel C01234567 --message "Hello from the CLI" --thread-ts 12345.6789
          python -m slackbot --channel C01234567 --dry-run

Send a message to Slack using a Bot User OAuth Token.

options:
  -h, --help            show this help message and exit
  --channel CHANNEL     Slack channel ID or name, for example C12345678 or #general. Channel ID is preferred.
  --message MESSAGE     Message text to send. Defaults to: 'Hello from slackbot!'
  --thread-ts THREAD_TS
                        Optional thread timestamp to reply inside an existing thread.
  --token TOKEN         Temporary Bot User OAuth Token override for this run (usually starts with xoxb-).
  --setup               Prompt for local Slack settings and save them in the repo directory.
  --dry-run             Print the message payload flow without calling Slack.
```

On the first real run, the CLI prompts for the Slack Bot User OAuth Token
(`xoxb-...`) and an optional default channel ID or name.

Storage layout:

- Bot User OAuth Token: `~/.slackbot/config.json`
- Per-repo default channel override: `.slackbot.json`

## Slack setup

1. Create a Slack app with a bot user.
2. Add the `chat:write` bot scope.
3. Install the app to your workspace.
4. Open `OAuth & Permissions`.
5. Copy the `Bot User OAuth Token`, which usually starts with `xoxb-`.
6. Run `python -m slackbot --setup` and paste that value when prompted.

If you want to post to a public channel without inviting the app first, you may
also need the `chat:write.public` scope. Otherwise, invite the bot to the
channel before posting.

Do not use `App ID`, `Client ID`, `Client Secret`, `Signing Secret`, or
`Verification Token` for this package. Those are not used for
`chat.postMessage`.

## Finding the channel value

You can pass either a channel name like `#general` or a channel ID like
`C12345678`, but channel ID is preferred.

One easy way to find a channel ID is to open Slack in a browser and look at the
URL for the channel: `https://app.slack.com/client/TXXXXXXX/CXXXXXXX`. The
`CXXXXXXX` segment is the channel ID.
