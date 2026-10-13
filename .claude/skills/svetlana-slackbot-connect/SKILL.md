---
name: svetlana-slackbot-connect
description: Use when the local Slack bot must start, reconnect, or be checked. Public template: configure private data sources before use.
---

# svetlana-slackbot-connect

## Purpose
Reusable, sanitized operating procedure for svetlana slackbot connect. This public version contains no client or owner records.

## Workflow
1. Check whether the bot is already healthy.
2. Start one supervised instance if absent.
3. Verify identity and channel allowlists.
4. Never post during a connectivity check.

## Calls and chain
Calls or hands off to: `team-comms`.

## Dependencies
`Slack, Node or Python bot runtime`

## Adapter note
Replace Slack with Teams, Discord, or another approved channel.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
