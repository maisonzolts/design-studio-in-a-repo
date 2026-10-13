---
name: inventory-counts-reconcile
description: Use when a document contains categorical counts, rollups, or a definition-of-done table. Public template: configure private data sources before use.
---

# inventory-counts-reconcile

## Purpose
Reusable, sanitized operating procedure for inventory counts reconcile. This public version contains no client or owner records.

## Workflow
1. Recount from the itemized source.
2. Check every subtotal against its parent total.
3. Separate current, archived, experimental, and adjacent items.
4. Refuse publication while any count is unreconciled.

## Calls and chain
Calls or hands off to: `none`.

## Dependencies
`none`

## Adapter note
No integration required.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
