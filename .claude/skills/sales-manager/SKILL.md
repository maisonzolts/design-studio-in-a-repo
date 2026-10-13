---
name: sales-manager
description: Use when pipeline, forecast, lead-stage, or revenue-priority review. Public template: configure private data sources before use.
---

# sales-manager

## Purpose
Reusable, sanitized operating procedure for sales manager. This public version contains no client or owner records.

## Workflow
1. Read current CRM stages and confirmed amounts.
2. Separate confirmed, probable, and speculative pipeline.
3. Identify next actions with evidence.
4. Never include private financial records in this repository.

## Calls and chain
Calls or hands off to: `status-update, opportunity-engine`.

## Dependencies
`HubSpot or another CRM`

## Adapter note
Replace CRM reads and your private financial thresholds.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
