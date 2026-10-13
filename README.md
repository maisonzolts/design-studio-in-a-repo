# Svetlana

Sanitized public-release template for a Claude Code executive-assistant and agency design-operations system.

This branch is an orphan: it carries no source-repository history. It contains reusable skills, a generic Claude Code prompt, templated MCP configuration, InDesign automation, a local cockpit shell, and a provenance-gated health-coach component. It contains no client deliverables, brand assets, memories, state, transcripts, financial records, or private strategy.

## Start here

1. Read `SANITIZATION_REPORT.md`.
2. Read `HANDOFF.md`.
3. Copy `.env.example` to a private `.env` and fill only the integrations you use.
4. Replace `<INDESIGN_MCP_ROOT>` in `.mcp.json`.
5. Install `requirements.txt` and, if you run the health tests or API, `health-app/requirements.txt`.
6. Run `python -m pytest`. The health tests import FastAPI from the health-app requirements. Cockpit tests are separate: `npm test` inside `cockpit/`.
7. Keep all real operational data in private stores outside this repository.

## What is included

- `.claude/skills/`: forty-five sanitized operating skills and a machine-readable map.
- `scripts/`: reusable InDesign, palette, brand-token, and health provenance tools.
- `cockpit/`: generic local dashboard code (originally written by Tom Lyons; MIT notice retained in `cockpit/LICENSE`).
- `health/` and `health-app/`: schema-only health coach example and validator API.
- `.mcp.json`: placeholder-only Claude Code MCP configuration.

## Safety

This is a framework, not a configured assistant. Review every skill, integration scope, privacy obligation, and approval boundary before use. Never put secrets or real client, health, financial, CRM, state, or transcript data in a public clone.
