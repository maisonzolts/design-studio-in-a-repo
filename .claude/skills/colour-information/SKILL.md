---
name: colour-information
description: Use when accurate HEX, RGB, CMYK, or spot-colour information is required. Public template: configure private data sources before use.
---

# colour-information

## Purpose
Reusable, sanitized operating procedure for colour information. This public version contains no client or owner records.

## Workflow
1. Read the source swatch through a colour-managed engine.
2. Record the engine-returned values and colour profile.
3. Do not invent spot-colour matches.
4. Pass digital combinations to palette-qa.

## Calls and chain
Calls or hands off to: `launch-indesign-mcp, palette-qa`.

## Dependencies
`InDesign colour engine`

## Adapter note
Use another colour-managed application; do not substitute naive formulas. scripts/brand_tokens.py can also read print-PDF vectors through optional PyMuPDF, which is not pinned in requirements.txt.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
