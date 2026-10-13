---
name: illustrator-batch-export
description: Use when batch export of logos, icons, patterns, or artboards from Illustrator. Public template: configure private data sources before use.
---

# illustrator-batch-export

## Purpose
Reusable, sanitized operating procedure for illustrator batch export. This public version contains no client or owner records.

## Workflow
1. Inspect the document and define export naming and formats.
2. Generate a reviewable .jsx file on disk; never hide it in an inline shell command.
3. Run against a copy or versioned source.
4. Verify counts, dimensions, colour mode, and untouched master artwork.

## Calls and chain
Calls or hands off to: `copyeditor`.

## Dependencies
`Adobe Illustrator, ExtendScript, Windows or macOS`

## Adapter note
Use Illustrator actions or another vector application's scripting API.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
