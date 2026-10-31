# StudyMind

StudyMind turns approved lecture notes or a text PDF into a summary, flashcards, practice questions and connected concepts. React 18 + Vite + Tailwind provide the interface; FastAPI, asynchronous SQLAlchemy, PostgreSQL, Alembic and Anthropic provide the API.

This patch replaces placeholder account/library screens and sample fallback results with persistent, private account flows. Missing services produce honest errors. It adds verification/recovery email, rotating sessions, password changes, account deletion/export, bounded PDF parsing, generation quotas and idempotency, tests and deployment configuration. It is a release candidate: complete the checks in [docs/RELEASE.md](docs/RELEASE.md) before announcing a launch.

## Local setup — macOS/Linux

Use Python **3.11 or 3.12** and Node **24**. `python3` must resolve to one of those supported Python versions; there is no requirement for a command named `python3.12`. PostgreSQL is required in production; local SQLite is supported for development.

Run from the repository root, after applying the patch:

```bash
python3 --version
node --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
python -c 'import secrets; print(secrets.token_hex(32))'
```

Paste the generated secret into `SECRET_KEY` in `backend/.env`. Set `ANTHROPIC_API_KEY` and an active `ANTHROPIC_MODEL` from your provider account. Configure SMTP for verification and recovery. Without AI configuration, saved sets remain usable but generation is disabled. Without SMTP, registration requiring verification and password recovery return 503. No development inbox, fake provider or hardcoded account is enabled in the deployed application.

For a local-only demonstration without email, set `REQUIRE_EMAIL_VERIFICATION=false` in `backend/.env`. Production settings reject this option. Never share a development instance publicly.

```bash
python -m alembic -c backend/alembic.ini upgrade head
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-proxy-headers --no-access-log
```

In a second terminal at the repository root:

```bash
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open <http://localhost:5173>. Keep the exact `localhost` host: the API rejects unexpected hosts/origins. Vite forwards `/api` to the backend. Production uses the same-origin proxy described in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

`backend/.env` is loaded from the repository root or backend directory. SQLite paths are relative to the command's working directory, so use the repository root consistently. The initial migration targets an empty database. Existing databases created by the original application need a backed-up, reviewed data migration; do not stamp them or drop their tables to bypass errors.

## Verification

```bash
source .venv/bin/activate
python -m pytest -q backend/tests
ruff check backend --select F401
ruff format --check backend
pip-audit -r backend/requirements-dev.txt --progress-spinner off
npm --prefix frontend run lint
npm --prefix frontend run test:unit
npm --prefix frontend run build
node scripts/audit-web.mjs
cd frontend
npx playwright install --with-deps chromium
npm run test:e2e
```

The e2e runner requires the activated Python environment and free ports 8000/5173. It runs a temporary SQLite database and an explicitly injected AI fixture in `scripts/e2e_server.py`. That QA server is excluded from the backend image. These tests verify the full UI/API flow, not live AI quality or email delivery. Playwright must download its matching browser after installation/upgrades; missing browser binaries are an environment failure, not a passing test.

PostgreSQL integration tests run when `TEST_DATABASE_URL` points to a **disposable dedicated** PostgreSQL database; they delete its StudyMind test users/jobs and verify real migrations, concurrent quotas, idempotency and atomic rate limits. Never use a production database. CI runs Python 3.11/3.12, PostgreSQL 16, frontend checks, Chromium accessibility/e2e, audits and image builds.

## API and data

- JSON routes live under `/api`; the OpenAPI document is `/api/openapi.json`.
- Register/login/refresh/logout, recovery and verification writes require a trusted `Origin` plus the CSRF nonce from `GET /api/auth/csrf`. Login uses JSON email/password, not an OAuth password form.
- Private routes require `Authorization: Bearer <access token>`. Tokens expire within 60 minutes and reference a revocable database session. Refresh cookies rotate and expire absolutely after seven days; access tokens stay in browser memory.
- `POST /api/generate` requires explicit `consent_to_provider: true`, source text of 50–12,000 characters, bounded options and an `Idempotency-Key`. Repeat the same key/payload to recover a result; a different payload with that key is rejected. Failed/expired jobs require a new generation intent.
- Up to 30 flashcards and 15 questions; PDFs up to 5 MiB/40 pages. Scanned, encrypted, malformed or oversized PDFs fail without fabricated material.
- Save a generation with `POST /api/studysets`, using its `generation_id`. Rename, list, fetch, export and delete saved sets under that prefix. Another user's identifiers return 404. Save at most 100 sets; pagination is bounded.
- Unsaved output is recoverable for one hour. Quota reservations cover a rolling 24 hours. The hourly maintenance command purges expired data; see the operations guide. Original source notes are saved only when the user chooses to include them.

## Security and release status

See [SECURITY.md](SECURITY.md), [docs/QA-UAT.md](docs/QA-UAT.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) and [docs/RELEASE.md](docs/RELEASE.md). Security checks reduce risk; they do not certify the application. Operator-specific SMTP, live AI, HTTPS/proxy behavior, database backup/restore, privacy policy and human UAT require evidence before launch. No keys, domains, human sign-offs or live-service results are invented by this patch.
