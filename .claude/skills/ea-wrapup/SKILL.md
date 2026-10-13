---
name: ea-wrapup
description: Use when session end, logging off, or explicit wrap-up. Public template: configure private data sources before use.
---

# ea-wrapup

## Purpose
Reusable, sanitized operating procedure for ea wrapup. This public version contains no client or owner records.

## Workflow
1. Reconcile completed, open, delegated, and blocked work.
2. Draft task/status updates and a team summary.
3. Require approval for external communication.
4. Save private continuation state; never commit it.

## Calls and chain
Calls or hands off to: `status-update, autosave`.

## Dependencies
`task manager, Slack, private state store`

## Adapter note
Replace Motion/Slack with your project and team tools.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
