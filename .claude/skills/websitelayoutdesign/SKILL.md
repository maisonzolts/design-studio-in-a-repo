---
name: websitelayoutdesign
description: Use when website wireframe, page layout, or approved web-design comp. Public template: configure private data sources before use.
---

# websitelayoutdesign

## Purpose
Reusable, sanitized operating procedure for websitelayoutdesign. This public version contains no client or owner records.

## Workflow
1. Load approved copy, brand tokens, page goal, and references.
2. Build a measured responsive comp.
3. Review each section through edit-design.
4. Emit a machine-readable build spec.
5. Hand approved output to developwebsite.

## Calls and chain
Calls or hands off to: `web-conversion-doctrine, design-best-practices, edit-design, developwebsite`.

## Dependencies
`HTML/CSS, Playwright; optional InDesign transfer`

## Adapter note
Use Figma or another measured layout surface if it can emit a build spec.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
