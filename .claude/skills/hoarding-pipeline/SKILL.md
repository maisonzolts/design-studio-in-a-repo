---
name: hoarding-pipeline
description: Use when asset intake starts or required materials are missing. Public template: configure private data sources before use.
---

# hoarding-pipeline

## Purpose
Reusable, sanitized operating procedure for hoarding pipeline. This public version contains no client or owner records.

## Workflow
1. Generate an asset checklist from deliverable requirements.
2. Catalog received files without embedding them in this repo.
3. Draft requests for missing material.
4. Start only reversible internal work until intake is complete.

## Calls and chain
Calls or hands off to: `identify-brand-identity, asset-population`.

## Dependencies
`Google Drive or file storage, Gmail`

## Adapter note
Replace storage and intake adapters.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
