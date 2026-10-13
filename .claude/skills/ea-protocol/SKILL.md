---
name: ea-protocol
description: Use when session start, daily briefing, catch-up, or agenda setting. Public template: configure private data sources before use.
---

# ea-protocol

## Purpose
Reusable, sanitized operating procedure for ea protocol. This public version contains no client or owner records.

## Workflow
1. Read calendar, inbox, task manager, and financial signals.
2. Present source-grounded sections sequentially.
3. Separate facts, risks, and recommendations.
4. Set the session agenda and hand production-ready work to project-pipeline.

## Calls and chain
Calls or hands off to: `account-manager, sales-manager, project-pipeline`.

## Dependencies
`Google Calendar, Gmail, Motion, Stripe`

## Adapter note
Replace each read adapter independently; preserve read-before-analysis order.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
