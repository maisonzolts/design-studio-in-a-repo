---
name: copyeditor
description: Use when proofreading, correctness, consistency, or final editorial QA. Public template: configure private data sources before use.
---

# copyeditor

## Purpose
Reusable, sanitized operating procedure for copyeditor. This public version contains no client or owner records.

## Workflow
1. Check facts and internal consistency.
2. Correct grammar, spelling, punctuation, and style.
3. Remove unsupported claims and generic AI phrasing.
4. Perform a clean final read after edits.

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
