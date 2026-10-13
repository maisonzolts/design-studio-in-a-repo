---
name: account-manager
description: Use when proactive account check-ins, stale client contact, or an account review. Public template: configure private data sources before use.
---

# account-manager

## Purpose
Reusable, sanitized operating procedure for account manager. This public version contains no client or owner records.

## Workflow
1. Read active accounts and last-contact dates.
2. Draft one factual update per due account.
3. Save drafts only; require approval before sending.
4. Record approved status changes through status-update.

## Calls and chain
Calls or hands off to: `ea-protocol, status-update`.

## Dependencies
`Gmail, CRM`

## Adapter note
Replace Gmail/CRM adapters with your mail and customer systems.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
