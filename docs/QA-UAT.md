# QA and user acceptance

Automated backend checks cover auth/token claims, normalization, CSRF/origins, session rotation/revocation, one-use recovery/verification links, account ownership/cascades, real PDF parsing/bounds, output validation, provider failure/retry behavior, idempotency, quotas and migration/model parity. Frontend unit checks cover refresh coalescing, bounded 401 retry and safe validation messages. Browser tests use the built SPA and a real temporary API/database with an explicit AI fixture, plus axe serious/critical checks. PostgreSQL tests exercise actual concurrent row locking and shared limiter increments. Fixtures do not certify live AI quality or email delivery.

Record browser/device, commit, date, tester, observed result and evidence for each scenario. A pass requires observed behavior, not an unchecked expectation. Automating axe covers only part of accessibility.

| Scenario | Expected acceptance |
|---|---|
| Register, existing address, resend, verify, wrong password, expired/reused link | Generic address-safe replies; real delivery; original chosen password needed to verify; expired/used links fail |
| Forgot password, reset, old sessions/tokens | Link arrives without token query logging; one use; previous password and all old sessions/links fail |
| Reload, two tabs, logout, password change, delete account | Session rotation works; logout revokes browser session; password change/account deletion revokes all; no cross-account notes/content appear |
| Notes 49/50/12,000/12,001 chars, counts and consent | Visible limits; no silent truncation; no provider request without explicit consent |
| Real PDFs, uppercase extension, scanned, encrypted, malformed, >5 MiB, >40 pages | Correct extraction or clear error; no hangs; temporary files removed; no partial hidden truncation |
| Provider timeout, invalid JSON, unavailable model, exhausted credit | Honest recoverable error; no fabricated output; no accidental unbounded retries |
| Double-click, slow response, stop waiting, repeat same payload/key | One reservation; completed draft recoverable; no duplicate saved set; cancellation is not promised to refund provider charges |
| Summary, flip, previous/next, short answers, multiple choice, concepts | Correct counts, usable recall; answers visible only on request; AI errors acknowledged and compared to source |
| Save without source, opt into source, rename, refresh deep link, paginate/delete, JSON export | Exact generated material preserved; source choice respected; exports contain only current user's data |
| Another user's set/draft UUID, unauthenticated routes | Denied consistently; no title/notes/content disclosure |
| Keyboard-only, screen reader, 200–400% zoom, reduced motion, light/dark | Visible focus, logical headings, named controls, usable tab arrows/Home/End, no keyboard trap or content loss |
| Mobile Safari and Chrome, desktop Safari/Firefox/Chromium | Responsive input/cards/tabs, readable contrast, actual cookie/refresh behavior tested |
| HTTPS domain, proxy, security headers, edge limits, logs | No secrets/body/token logging; first-party Secure cookies; trusted hosts only; spoofed forwarding cannot bypass limits |
| PostgreSQL concurrency, restart during generation, cleanup failures | Budget reservations preserved; stale jobs fail safely; process restarts retain saved sets; cleanup alert fires |
| Backup restore and account deletion | Staging restore validated; recovery objectives measured; live deletion cascades; backup retention documented |

Use at least three permitted academic topics and all three difficulty levels for the live AI review. Evaluate factual grounding, useful explanations, non-duplicate cards, fair multiple-choice options, instruction injection in source, unsupported citations and requested counts. Establish an agreed quality threshold and budget with the owner before approval. Do not send real sensitive student material during testing.
