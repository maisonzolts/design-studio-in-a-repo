---
name: palette-qa
description: Use when a palette needs WCAG and light/dark usability checks. Public template: configure private data sources before use.
---

# palette-qa

## Purpose
Reusable, sanitized operating procedure for palette qa. This public version contains no client or owner records.

## Workflow
1. Test every intended foreground/background pair.
2. Report normal and large-text thresholds.
3. Suggest hue-preserving alternatives without changing approved source colours.
4. Require human judgment before adopting alternatives.

## Calls and chain
Calls or hands off to: `scripts/palette_qa.py`.

## Dependencies
`Python`

## Adapter note
Any standards-compliant contrast engine can replace the script.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
