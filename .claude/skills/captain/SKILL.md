---
name: captain
description: Use when system status board, capability inventory, or build audit. Public template: configure private data sources before use.
---

# captain

## Purpose
Reusable, sanitized operating procedure for captain. This public version contains no client or owner records.

## Workflow
1. Inventory system work only, not client records.
2. Classify blocked, broken, active, scheduled, parked, and complete.
3. Attach evidence for status claims.
4. Reconcile all counts before publishing the board.

## Calls and chain
Calls or hands off to: `inventory-counts-reconcile`.

## Dependencies
`Git, local project metadata`

## Adapter note
Use your issue tracker or project database as the status source.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
