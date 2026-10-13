---
name: meeting-ingest
description: Use when a meeting summary or transcript arrives. Public template: configure private data sources before use.
---

# meeting-ingest

## Purpose
Reusable, sanitized operating procedure for meeting ingest. This public version contains no client or owner records.

## Workflow
1. Verify the meeting and participants from approved sources.
2. Extract decisions, commitments, dates, and status changes.
3. Update private project/brand context.
4. Draft follow-ups and route production work without sending.

## Calls and chain
Calls or hands off to: `status-update, project-pipeline`.

## Dependencies
`Gmail, Motion or another note taker, CRM`

## Adapter note
Replace the meeting-note and CRM adapters.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
