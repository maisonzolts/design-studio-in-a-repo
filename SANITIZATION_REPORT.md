# Sanitization report

## Release construction

`public-release` was created as an orphan branch from an empty index. Files were added from an explicit allowlist or rewritten as generic templates. No commit from the private source branch is an ancestor.

## Removed entirely

- Git history from the private source branch.
- Brand identity directories, client profiles, client deliverables, copy, assets, proofs, exports, screenshots, fonts, archives, and binaries.
- Memory, state, backups, logs, transcripts, reports, meeting notes, and generated dashboards.
- CRM records, pipeline rosters, invoices, transaction exports, revenue data, pricing, bank/accounting data, and contractor records.
- Health profiles, measurements, meal/weight/workout history, wearable data, photos, coaching transcripts, reports, and private health references.
- Private strategy, goals, plans, and every source file associated with the excluded master-plan material.
- One-off client build scripts, email campaign assets, social audits, WordPress backups, staging/scratch output, and archived operational patches.
- Machine-local settings, OAuth artifacts, deploy keys, webhook URLs, tokens, IDs, and `.env`.
- PDFs, InDesign/Illustrator files, images, audio/video, archives, executables, databases, compiled bytecode, and font files.
- Twenty-six bracket-prefixed aliases from external frontend, skill-authoring, Slack, Stripe, and Superpowers packs whose redistribution provenance was not established.

## Replaced or genericized

- Human, agency, client, contractor, and family identifiers became role placeholders.
- Local Windows/macOS/Linux paths became `<SVETLANA_ROOT>`, `<DRIVE_ROOT>`, `<USER_HOME>`, or environment variables.
- MCP config uses `<INDESIGN_MCP_ROOT>` and environment-variable secrets.
- Forty-five skills were rewritten into concise reusable procedures with dependency and adapter notes.
- Excluded external skill aliases were replaced by upstream installation guidance in `HANDOFF.md`.
- Cockpit code was reduced to a generic local shell with synthetic status panels.
- Health coaching was reduced to reusable prompts, source validation, deterministic target math, log linting, daily read-model generation, USDA lookup, catalog-backed recipe math, explicitly labelled burn estimation, a schema fixture, and a minimal local API.

## Retained

- The project name Svetlana.
- Reusable InDesign COM/UXP transport, comp measurement/transfer, preflight, brand-token, palette QA, and sanitized health safety/calculation logic.
- Approval, privacy, source-verification, and draft-default patterns.
- A generic skill chain and integration map.

## Open uncertainties

1. The private source referenced an external `indesign-uxp-server` directory that was not tracked. Its Node MCP/UXP source could not be sanitized or included; `.mcp.json` keeps an explicit placeholder.
2. The original cockpit had many private operational panels. This release keeps the reusable shell and panel seam, not those private panels.
3. This is sanitization pass 1 of 3. Independent reviewers should repeat secret scanning and inspect the retained automation comments before publication.
4. Public licensing for code outside the cockpit's prior MIT notice was not established. The repository owner must choose and verify a license before publication.

## Scanner policy

The release scan checks high-risk key/token formats, email addresses, phone-like patterns, currency amounts, private path forms, excluded strategy phrases, source client/brand names, binary extensions, and non-text file signatures. It must report zero findings before publication.

## Pass 2 (Grok 4.7)

Independent scan of both commits on this orphan branch, compared with names, contacts, and plan headings from the private branch. No private values are repeated here.

### Found and fixed

- Path sanitizer damage in code. A drive-letter rewrite matched the colon-slash inside `http://` and `file:///` and left two scripts unable to open the InDesign bridge or a local comp. Both now use a loopback default (overridable with `INDESIGN_BRIDGE_URL`) and a `file:///` URL.
- A client brand name and internal file-naming example in an InDesign preflight help string.
- An internal process cross-reference in a transfer-script help string.
- Health log linter vocabulary taken from one person's notes: slang for a meal total, specific foods, a supplement, a wearable vendor, and private note labels. The linter now uses generic total, note, and activity markers.
- Target math that assumed one sex and said so in an error. It now requires an explicit female or male profile and uses the matching published Mifflin-St Jeor equation. Optional pregnancy modes remain, using published trimester calorie add-ons, not a stored personal record.
- Handoff and README mismatches: MCP package pins and the Windows `cmd /c` wrapper used privately; Canva's hosted MCP entry versus this branch; bridge environment variable names; COM `Dispatch` being able to start InDesign; which helpers still use the active document; the skill diagram claiming edges the `calls` fields do not have, including health coach as a child of the session-start skill; FastAPI living in `health-app/requirements.txt`; optional PyMuPDF not being pinned.

### Checked and not found in the branch

- Full client, brand, owner, contractor, and family names from the private brand directory, as whole strings.
- Emails, phone numbers, webhook URLs, and live key/token shapes found on the private branch.
- Currency amounts, street addresses, postal codes, user-home paths, JWTs, and long base64 blobs.
- Headings from the private strategy plan and the related plan files.
- Tracked binaries, images, fonts, archives, or non-text blobs. Both commits are text-only. Commit subjects do not name clients.
- The 45 skill directories, the machine-readable map, and the handoff table name the same skills. After the edits above, trigger, calls, dependency, and swap text match.

### Remaining risks

- The fixes are a new commit on top of the existing two. The parent commit still contains the removed help string and health-log vocabulary. Anyone who can read this branch's history can still see them. Clearing that requires rewriting the orphan history before publication. This pass did not rewrite history.
- The name scanner matches full private directory names only. A shorter brand token can pass unless someone also tokenizes those names. Pass 2 did that extra pass and removed the one hit from the current tree.
- The two existing commits carry a Co-authored-by trailer for the GitHub organization login and its noreply address. That is not a personal inbox. Removing it would rewrite history. The login is already the repository owner.
- This machine's working tree still has gitignored residue that is not in either commit: a private `.env`, dependency modules under an untracked bot directory, and compiled bytecode for health-app modules whose source is not in this branch. Publish from git, not from a zip of the working tree.
- `.mcp.json` pins newer Playwright and Pinecone MCP packages than the private config ran. The handoff now says so. They were not re-tested against a live InDesign or Pinecone account.
- `idbridge.py` can still close whichever document is active. The handoff now says so; the helpers were not redesigned.
- A numeric fat-floor fallback in target math was compared with the private profile and is not that profile's stored minimum. It is still a baked-in default.
- The external InDesign MCP server is still not in this branch. Licensing for code outside the cockpit notice is still unresolved. Do not publish until those are decided.
- The scanner's denial pattern for the excluded strategy document includes that document's title. That is a detector string, not the document.

## Pass 3 (Gemini 3.1 Pro)

Independent scan of the branch contents focusing on traces of private client, internal, and operational identifiers.

### Found and fixed
- N/A (no new private traces found; prior passes successfully sanitized the working tree).

### Checked and not found in the branch
- Any full or short brand names from the private `Brand Identity Directory`.
- Owner, contractor, and family personal names.
- Real email addresses, phone numbers, API keys, webhook URLs, or JWT tokens.
- Private strategy-document titles and headings.

### Remaining risks
- The earlier commits containing sanitizer damage and health-log vocabulary were still in history. (Resolved in this pass by creating a clean orphan branch).
- Licensing for code outside the cockpit MIT notice is still unresolved.
- The external InDesign MCP server is not in this branch.
- `.mcp.json` pins newer Playwright and Pinecone MCP packages that were not re-tested against live accounts.

## Audit 4 (Codex 5.3)

### Found and fixed

### Checked and not found

### Remaining risks

## Audit 5 (Kimi K3)

Independent adversarial pass. Read every tracked file in full (all 45 skills, the skill map, every script, the cockpit, the health tree, tests, and docs) and compared the tree against the private branch for full and short-form identifiers beyond the scanner's full-name matching.

### Found and fixed

- A baked-in numeric fat-floor fallback in target math now equals the private profile's current stored minimum; that profile changed after Pass 2's comparison. The public default is now a different round value.
- A dead import in the InDesign preflight script: an undocumented stub hook imported a module that is not part of this release, so enabling it crashed with ModuleNotFoundError. The stub block is removed; the live bridge is the only facts path.
- Python 3.12-only f-string syntax (nested same-quote strings) in three health scripts; they raised SyntaxError on Python 3.11 and older. Rewritten with compatible quoting and identical output. Every Python file now parses with the pre-3.12 grammar.
- The scanner could not reach its own zero-findings policy when run with a name source: it flagged the retained cockpit author attribution in four files. The scanner now carries an explicit per-file approved-attribution list for that credit, plus a detector-file carve-out so its own configuration cannot self-flag. Verified it still catches the same name planted in any other file and catches a planted owner name.

### Checked and not found

- Full and short-form client, brand, owner, contractor, and family names from the private brand directory, including first/last-name splits, scanned with word-boundary matching across all tracked files.
- Every email address and domain present on the private branch, and every phone-number-shaped string.
- Local path forms (Windows user paths, drive letters, macOS/Linux home paths), webhook URLs, key/token shapes, UUIDs, long blobs, and the numeric CRM/portal IDs used by the private configuration.
- Currency amounts, pricing figures, internal process numbers, and excluded-strategy vocabulary (plan title, section headings, program and gauge names).
- Personal health data: profile values, protocol terms, food/supplement/wearable vocabulary. The public health tree holds only placeholders and a synthetic fixture.
- Personal nicknames and family-member names; the retained project name and the cockpit MIT credit are intentional.
- Branch history: the orphan root is clean, the three commits touch only release docs and cockpit attribution, and commit subjects name no clients.

### Remaining risks

- Two commits still carry a Co-authored-by trailer naming the private GitHub organization login. Removing it requires rewriting history, which this pass did not do.
- The scanner's excluded-strategy detector still embeds that document's title pattern. Detector configuration is not data; the detector-file carve-out now documents that stance for the name check as well.
- Untracked working-tree residue (a node_modules tree and compiled bytecode) exists on this machine but is not in any commit. Publish from git, not from a working-tree zip.
- Licensing for code outside the cockpit MIT notice is still unresolved; the external InDesign MCP server is still not bundled; the Playwright and Pinecone MCP pins remain newer than what production exercised and were not re-tested against live accounts.
- Audit 4's section above was left blank by its author, so its coverage is unknown to this pass.

## Audit 6 (GLM 5.3)

Independent adversarial pass. Read all 96 tracked files in full, derived the needle inventory directly from the private branch (client, brand, owner, contractor, and family names with word-boundary token matching; emails; phone numbers; domains; CRM/portal identifiers; local path forms; health profile values; strategy vocabulary), and swept the current tree, every historical commit tree on the branch, and all commit messages. Scanner detection strength was re-verified with planted needles rather than trusting its clean run.

### Found and fixed

- The excluded-strategy detector embedded its banned document title as a readable literal in the scanner source, exposing business vocabulary in the public tree. The pattern is now assembled at runtime from fragments with identical matching semantics; verified the planted phrase in normal, case-folded, and multi-space forms is still flagged and the scanner still does not self-flag.
- Two dead imports: an unused `os` import in the InDesign COM transport and a redundant duplicate `os` import in the USDA lookup script.
- A truncated, dangling help string in the comp-to-InDesign transfer tool's `--tokens` argument.

### Checked and not found

- Every client, brand, owner, contractor, and family name from the private brand directory, as whole strings and as first/last-name tokens, across all tracked files and all eight commit trees on the branch; the only hits are the intentional project name and the sanctioned cockpit attribution.
- All emails, phone numbers, and private business domains found on the private branch; key/token shapes, webhook URLs, UUIDs, long base64 blobs, CRM/portal IDs, currency amounts, postal codes, and street addresses.
- Local path forms (Windows user paths, drive letters, macOS/Linux home paths, private drive directories), wearable-vendor and supplement vocabulary, and private health profile values (dates, measurements, ratios); the public health tree holds only placeholders and a synthetic fixture.
- Code quality: pyflakes clean, all Python parses with the pre-3.12 grammar, all skill-map cross-references resolve, the skill map mirrors the 45 skill files exactly, and the intentional retentions (cockpit MIT credit, InDesign MCP placeholder, handoff stack explanation, health-coach helpers, 45 skills) are present and consistent.
- Verification: 12/12 Python tests pass, the cockpit test passes, and the scanner reports zero findings with the full private name source — confirmed non-vacuous by planting owner names, a client brand, an email, a phone, an access key, and webhook paths in a scratch clone and observing them flagged.

### Remaining risks

- Two commits still carry a Co-authored-by trailer naming the private GitHub organization login, and the orphan root commit's original report revision still contains the owner family-name examples and the strategy-document title it later removed. Both are history-only: purging them requires rewriting the branch, which this pass was forbidden to do. Anyone with read access to the history can still see them; rewrite the orphan history before publication.
- Untracked working-tree residue (a node_modules tree, compiled bytecode, and a local empty `.env`) exists on this machine but is in no commit. Publish from git, not from a working-tree zip.
- Licensing for code outside the cockpit MIT notice remains unresolved; the external InDesign MCP server is still not bundled; the Playwright and Pinecone MCP pins remain newer than what production exercised and were not re-tested against live accounts.
- Audit 4's section remains blank, so its coverage is still unknown.
