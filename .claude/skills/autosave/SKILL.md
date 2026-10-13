---
name: autosave
description: Use when periodic save checkpoints or context-compaction risk. Public template: configure private data sources before use.
---

# autosave

## Purpose
Reusable, sanitized operating procedure for autosave. This public version contains no client or owner records.

## Workflow
1. Summarize current task, decisions, blockers, and next action.
2. Write only to a private ignored state file.
3. Never include credentials or client data in a public tree.

## Calls and chain
Calls or hands off to: `none`.

## Dependencies
`local filesystem`

## Adapter note
Point the state path at your own private, ignored store.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
