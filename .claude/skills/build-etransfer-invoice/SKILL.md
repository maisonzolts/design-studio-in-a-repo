---
name: build-etransfer-invoice
description: Use when an approved billing milestone requires an invoice draft. Public template: configure private data sources before use.
---

# build-etransfer-invoice

## Purpose
Reusable, sanitized operating procedure for build etransfer invoice. This public version contains no client or owner records.

## Workflow
1. Verify the contract milestone and billing identity.
2. Select the approved payment rail and tax treatment.
3. Create a draft invoice from placeholders and read it back.
4. Require owner approval before issuing or sending.

## Calls and chain
Calls or hands off to: `copyeditor`.

## Dependencies
`accounting provider, Stripe or bank transfer, optional InDesign`

## Adapter note
Replace payment rails and tax rules with your jurisdiction and accounting tool.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
