---
name: identify-brand-identity
description: Use when brand ingestion or the first brand-matched deliverable. Public template: configure private data sources before use.
---

# identify-brand-identity

## Purpose
Reusable, sanitized operating procedure for identify brand identity. This public version contains no client or owner records.

## Workflow
1. Inventory supplied and public brand sources.
2. Extract approved logos, typography, colours, imagery rules, voice, and constraints.
3. Mark source and confidence for each fact.
4. Write a private brand profile outside this public template.

## Calls and chain
Calls or hands off to: `palette-qa`.

## Dependencies
`file storage, web/browser access`

## Adapter note
Replace local-drive and web-source adapters.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
