---
name: newsletter-build
description: Use when newsletter content and design production. Public template: configure private data sources before use.
---

# newsletter-build

## Purpose
Reusable, sanitized operating procedure for newsletter build. This public version contains no client or owner records.

## Workflow
1. Confirm audience, purpose, content, and approved template.
2. Build conservative email HTML.
3. Run copy, links, size, accessibility, and client rendering checks.
4. Hand approved output to email-send.

## Calls and chain
Calls or hands off to: `email-workflow, edit-design, copyeditor, email-send`.

## Dependencies
`ESP, HTML email tooling`

## Adapter note
Replace Mailchimp with your ESP; retain rendering and consent checks.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
