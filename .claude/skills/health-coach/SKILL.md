---
name: health-coach
description: Use when food, meal, nutrition, weight, body-composition, workout, or health check-in. Public template: configure private data sources before use.
---

# health-coach

## Purpose
Reusable, sanitized operating procedure for health coach. This public version contains no client or owner records.

## Workflow
1. Load the private profile and today's private log.
2. Resolve every nutrition number to a catalog entry with an allowed source.
3. Validate the entire catalog before quoting or logging macros.
4. Lint meal logs and regenerate daily read models from their owned food and burn sources.
5. Calculate portions and recipe totals from catalog values only.
6. Compute targets with Mifflin-St Jeor for the profile's stated sex. Do not assume a sex.
7. Mark burn estimates as estimates and exclude them from measured-history training data.
8. Write private logs outside the public repo.
9. Do not diagnose or replace medical care.

## Calls and chain
Calls or hands off to: `scripts/health_validate.py`, `scripts/health_targets.py`,
`scripts/health_log_lint.py`, `scripts/health_daily_union.py`,
`scripts/health_usda.py`, `scripts/_health_meal_calc.py`, and
`scripts/burn_estimate.py`.

## Dependencies
`Python, PyYAML, sourced catalog; optional USDA_API_KEY`

## Adapter note
Replace fitness providers freely, but never replace the catalog provenance validator.

## Safety
- Read before writing.
- Keep credentials in environment variables.
- Keep client, health, financial, and state data outside this repository.
- External messages, publishing, scheduling, CRM writes, and financial actions require explicit human approval.
