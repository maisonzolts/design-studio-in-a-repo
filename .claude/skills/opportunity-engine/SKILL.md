---
name: opportunity-engine
description: Use when revenue-move review or an approved deliverable/deal creates a follow-up opportunity. Public template: configure private data sources before use.
---

# opportunity-engine

## Purpose
Reusable, sanitized operating procedure for opportunity engine. This public version contains no client or owner records.

## Workflow
1. Read current consented CRM records.
2. Identify evidence-based next offers or follow-ups.
3. Rank by fit and timing, not vanity metrics.
4. Draft actions only; commercial messages require consent and approval.

## Calls and chain
Calls or hands off to: `sales-manager, status-update`.

## Dependencies
`CRM`

## Adapter note
Replace the CRM query adapter.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
