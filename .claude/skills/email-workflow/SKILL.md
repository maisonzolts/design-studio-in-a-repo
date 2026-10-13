---
name: email-workflow
description: Use when newsletter, campaign, nurture, automation, template, or list-hygiene work. Public template: configure private data sources before use.
---

# email-workflow

## Purpose
Reusable, sanitized operating procedure for email workflow. This public version contains no client or owner records.

## Workflow
1. Classify template, one-off campaign, sequence, automation, or hygiene.
2. Verify audience consent and suppression rules.
3. Route builds to newsletter-build and delivery to email-send.
4. Keep all live actions approval-gated.

## Calls and chain
Calls or hands off to: `newsletter-build, email-send`.

## Dependencies
`ESP, CASL-compliant consent records`

## Adapter note
Replace the ESP while retaining consent, suppression, and approval gates.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
