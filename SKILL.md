---
name: slackbot
description: Send short Slack messages from Codex or the terminal using this repository's Slack bot CLI. Use this skill when the user wants to post a status update, regression result, checkpoint notification, or other simple text message to Slack.
---

# SlackBot

Use this skill when a task needs to send a concise Slack message from the local workspace.

## Workflow

1. Check whether the user wants an actual Slack post or just a dry run.
2. If Slack credentials or channel details are unclear, read `references/setup.md`.
3. Use the wrapper script:

```bash
python3 scripts/send_message.py --channel C01234567 --message "Build passed"
```

4. For verification without calling Slack, use:

```bash
python3 scripts/send_message.py --channel C01234567 --message "Build passed" --dry-run
```

## Notes

- The first real run prompts for the Slack Bot User OAuth Token and saves it in `~/.slackbot/config.json`.
- The repo-local `.slackbot.json` is only for per-repo defaults such as `default_channel`.
- Prefer channel IDs over channel names.
- Keep messages short and operational.
- For Slack credential details and channel discovery, read `references/setup.md`.
