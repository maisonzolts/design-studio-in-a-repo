---
name: offload
description: Use when work should be captured for later rather than done now. Public template: configure private data sources before use.
---

# offload

## Purpose
Reusable, sanitized operating procedure for offload. This public version contains no client or owner records.

## Workflow
1. Look up context before asking questions.
2. Specify outcome, inputs, constraints, acceptance criteria, and next review.
3. Create a draft task assigned to the configured owner role.
4. Do not silently schedule or message anyone.

## Calls and chain
Calls or hands off to: `delegation-oscillation`.

## Dependencies
`Motion or another task manager`

## Adapter note
Replace task creation with your queue system.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
