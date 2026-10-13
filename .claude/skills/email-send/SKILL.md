---
name: email-send
description: Use when an approved email is ready for delivery preparation. Public template: configure private data sources before use.
---

# email-send

## Purpose
Reusable, sanitized operating procedure for email send. This public version contains no client or owner records.

## Workflow
1. Confirm written approval and audience consent.
2. Create a new campaign from approved HTML.
3. Run link, rendering, sender, and unsubscribe checks.
4. Send a test only; require explicit approval to schedule or send live.

## Calls and chain
Calls or hands off to: `email-workflow, copyeditor`.

## Dependencies
`Mailchimp or another ESP`

## Adapter note
Replace campaign creation and test-send adapters with your ESP.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
