# Verification record — 2026-10-31

Patch baseline: Hazmat-ai/StudyMind main commit `2f04bdb868e65177e1a2e9a3baf82d0154b28536`.

Local environment: Linux, Python 3.12.14 and Node 24.22.1. No production credentials were supplied, no paid AI request was made, and nothing was deployed or pushed to GitHub.

| Check | Observed result |
|---|---|
| Backend pytest | **35 passed, 1 skipped**; skipped test requires a dedicated PostgreSQL server |
| Alembic upgrade + metadata check | Passed against a fresh SQLite database, included in pytest |
| Real PDF parsing | Passed valid/malformed/signature, blank/OCR, size, encrypted, page count and busy-capacity cases |
| Retention and global budget | Passed cleanup preserving saved material/current budget; deleting an account cannot reset global cost reservations |
| Ruff unused-import check and formatting | Passed |
| Python compilation | Passed for backend and scripts |
| Frontend ESLint | Passed |
| Frontend session unit tests | **3 passed** |
| Vite production build | Passed |
| Python runtime/development dependency audit | No known advisories reported for the pinned requirements |
| npm runtime dependency audit | No vulnerabilities reported with `--omit=dev` |
| Full npm audit | Remaining moderate minimatch development-tooling advisory; explicitly reported by audit wrapper; exception expires 2026-11-30 |
| YAML/JSON configuration parsing | Passed; this is not a Docker/hosting deployment test |
| Vercel configuration generator | Correct `/api` destination and HTTPS-only validation observed |
| Release approval guard | Correctly refuses missing release evidence; no human gate marked approved |
| Browser/e2e/axe | **Blocked**: API and built-preview servers started, but matching Chromium executable was unavailable. Browser download repeatedly returned an invalid/truncated archive. All three tests stopped at browser launch, before assertions. No accessibility pass is claimed. |
| PostgreSQL concurrency/migration integration | Not run locally; dedicated test and PostgreSQL 16 CI service included |
| Python 3.11 execution | CI matrix included; local runtime was 3.12. Final pinned runtime dependencies resolved for Python 3.11; actual 3.11 CI remains required. |
| Container builds/Caddy runtime/Compose/Railway/Vercel | Not run locally; Docker unavailable. CI build/config validation and operator instructions included. |
| SMTP, live Anthropic/model quality, restore drill, human UAT | Pending operator configuration and observed evidence |

Passlib emits a Python 3.12 `crypt` deprecation warning. Supported Python versions are explicitly 3.11/3.12; this patch does not claim Python 3.13 compatibility.

Apply integrity is checked separately when packaging: `git apply --check`, actual application against the pristine baseline, and comparison of every changed file. A clean patch application is not a substitute for CI against the final GitHub commit. Complete `docs/RELEASE.md` before launch.
