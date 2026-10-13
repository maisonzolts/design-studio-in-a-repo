---
name: paintbrush
description: Use when an approved layout needs brand colour and typography applied. Public template: configure private data sources before use.
---

# paintbrush

## Purpose
Reusable, sanitized operating procedure for paintbrush. This public version contains no client or owner records.

## Workflow
1. Load approved brand tokens.
2. Map semantic roles to named swatches and text styles.
3. Apply colour and typography only.
4. Review through edit-design, then hand off assets to asset-population.

## Calls and chain
Calls or hands off to: `identify-brand-identity, colour-information, edit-design, asset-population`.

## Dependencies
`InDesign or target design tool`

## Adapter note
Replace swatch/style APIs for the target application.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
