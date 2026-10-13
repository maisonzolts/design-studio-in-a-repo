---
name: status-update
description: Use when a lead, client, deal, or project gains a status-relevant fact. Public template: configure private data sources before use.
---

# status-update

## Purpose
Reusable, sanitized operating procedure for status update. This public version contains no client or owner records.

## Workflow
1. Extract only explicit status facts.
2. Read the existing record first.
3. Prepare a minimal patch with provenance.
4. Require approval before writing external CRM data.

## Calls and chain
Calls or hands off to: `sales-manager`.

## Dependencies
`HubSpot or another CRM`

## Adapter note
Replace CRM writes with your system's reviewed upsert.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
