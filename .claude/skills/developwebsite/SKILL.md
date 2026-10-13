---
name: developwebsite
description: Use when an approved web build specification is ready for implementation. Public template: configure private data sources before use.
---

# developwebsite

## Purpose
Reusable, sanitized operating procedure for developwebsite. This public version contains no client or owner records.

## Workflow
1. Validate the approved build spec.
2. Build tokens and reusable components before pages.
3. Populate approved copy and assets.
4. Test responsive behavior, accessibility, forms, and analytics without publishing.

## Calls and chain
Calls or hands off to: `web-conversion-doctrine, websitelayoutdesign, edit-design, asset-population`.

## Dependencies
`WordPress/Elementor, browser automation`

## Adapter note
Replace the CMS adapter with Webflow, a framework, or another builder.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
