---
name: project-pipeline
description: Use when a new internal or client deliverable starts. Public template: configure private data sources before use.
---

# project-pipeline

## Purpose
Reusable, sanitized operating procedure for project pipeline. This public version contains no client or owner records.

## Workflow
1. Classify the deliverable and responsible role.
2. Ingest brand, copy, assets, and constraints.
3. Route to the correct production skill.
4. Record review outcomes and remaining work in private state.

## Calls and chain
Calls or hands off to: `delegation-oscillation, identify-brand-identity, marketing-deliverable, ea-wrapup`.

## Dependencies
`task manager and private project state`

## Adapter note
Replace Motion/private state with your project system.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
