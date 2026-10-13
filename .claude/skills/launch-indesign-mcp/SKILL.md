---
name: launch-indesign-mcp
description: Use when InDesign automation is needed or its connection fails. Public template: configure private data sources before use.
---

# launch-indesign-mcp

## Purpose
Reusable, sanitized operating procedure for launch indesign mcp. This public version contains no client or owner records.

## Workflow
1. Try a real COM round-trip first.
2. If COM is unavailable, post to INDESIGN_BRIDGE_URL (default http://127.0.0.1:3000).
3. Treat a returned value as health; do not trust a status flag alone.
4. Never close or overwrite a document the agent did not open.

## Calls and chain
Calls or hands off to: `scripts/idbridge.py, scripts/idcom.py`.

## Dependencies
`Windows, Adobe InDesign, pywin32; optional external UXP/MCP bridge`

## Adapter note
On non-Windows hosts, set INDESIGN_BRIDGE_URL and use the external UXP bridge or another InDesign automation host. Set SVETLANA_ID_TRANSPORT to com, http, or auto.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
