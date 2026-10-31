# Deployment and operations

## Preflight

Use an empty PostgreSQL 16 database with private network access and verified TLS when crossing untrusted networks. Back up existing data before any upgrade. The initial `0001` migration cannot adopt the original unversioned database in place. Existing users/content require a separately reviewed schema/data migration and password/email-verification policy. Do not auto-stamp, reset, or drop a live database.

Generate independent signing, proxy and database secrets with `python -c 'import secrets; print(secrets.token_hex(32))'`. Store them in the platform secret manager, never Git or frontend VITE variables. Use 64 hex characters for the Compose database password so it is safe in the connection URL; otherwise URL-encode reserved password characters yourself. Provider keys, SMTP passwords, database URLs and the proxy token are backend/edge secrets. Only public API routing configuration goes to the frontend.

Required production environment: `APP_ENV=production`, `SECRET_KEY`, `DATABASE_URL`, canonical HTTPS `WEB_ORIGIN` and `API_ORIGIN`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`. Email verification is always required in production. The app starts without AI/mail credentials to permit recovery of saved sets, but launch gates require working generation, registration and recovery. Select an available model in your Anthropic account, confirm pricing and output quality; no model ID is assumed permanently active. The original Claude Sonnet 4 model was retired.

## Railway API and Vercel SPA

1. Create a Railway PostgreSQL service. Point a backend service at this repository with **root build context**, `backend/Dockerfile` and `backend/railway.json` as its config path. Do not set build context to `backend` while using these COPY paths. Populate secrets, `DATABASE_URL` and `API_ORIGIN=https://your-api.up.railway.app`.
2. Set `WEB_ORIGIN` to your exact public frontend origin. Configure DNS/domain ownership before issuing verification links. `postgres://` and `postgresql://` URLs are normalized to asyncpg; provider `sslmode=require` is normalized to `ssl=require`. Confirm actual provider TLS/certificate requirements in staging.
3. From the repository root, create the public Vercel configuration:

   ```bash
   PUBLIC_API_ORIGIN=https://your-api.up.railway.app node scripts/configure-vercel.mjs
   ```

   Review and commit `frontend/vercel.json`, then set Vercel's project root to `frontend`, Node 24, build `npm run build`, output `dist`. Leave `VITE_API_URL` unset (defaults to `/api`). Never put secrets into Vercel's browser build variables. The API rewrite preserves `/api` and precedes the SPA fallback; security headers apply to page responses.
4. Railway's pre-deploy command runs `alembic upgrade head`; startup verifies the revision and database connectivity. No automatic create_all occurs outside the explicitly testing-only configuration. Roll out one migration job, then compatible API workers. If your service configuration does not load the supplied Railway config, enter the pre-deploy/start commands manually from it.
5. This Vercel rewrite does not inject a private authenticated IP header. Keep `PROXY_TOKEN` empty. Uvicorn ignores all forwarded IP headers; app IP limits may aggregate users behind the platform proxy. Per-account and global generation quotas still apply. Before larger public traffic, configure and verify edge request/body/rate limits and trusted client-IP forwarding. Never trust a client-supplied X-Forwarded-For header. A custom proxy can supply `X-Real-IP` only if it also overwrites `X-StudyMind-Proxy-Token` with a private shared token and prevents backend bypass.
6. Test frontend HTTPS, first-party `__Host-` cookies, refreshing after reload, deep links, `/api` error handling and verification/reset email fragments on the exact public domain. Cross-site direct browser calls to the Railway origin are rejected by design.

Railway runtime receives `PORT`; the supplied start command honors it and disables access/forwarded-header logging. `GET /api/health` checks the database, not Anthropic or SMTP. Monitor generation/error rates and email delivery separately.

## Optional self-hosted Compose

Copy root `.env.example` to `.env`, fill all secrets/domain/provider/mail values, point DNS at the host and allow inbound 80/443. Review firewall, TLS, resource limits and backup storage before use.

```bash
cp .env.example .env
# Edit .env before running the following command.
docker compose up --build -d
```

Only Caddy exposes host ports. The API has a non-root user, read-only root filesystem, bounded temporary storage/memory/processes and dropped capabilities. Caddy overwrites the trusted proxy headers and uses the same public host for API and SPA. Caddy manages TLS. One parser subprocess per API worker is permitted at a time; busy requests return 429. Size memory for each worker’s parser allowance before changing the worker count. Protect the Docker host and secrets; Compose is a deployment option, not a managed high-availability platform. Image builds/configuration were not locally verified where Docker was unavailable; CI includes builds and Caddy validation.

## Scheduled cleanup, retention and backups

Run `python -m app.maintenance` **from backend**, hourly, with the same environment and database as the API. On Railway create a scheduled service using the backend image/command; for Compose run `docker compose exec -T api python -m app.maintenance` from the host scheduler. Alert on failures. Jobs become inaccessible after one hour even before cleanup; physical output removal can take up to another cleanup interval. Quota fingerprints survive the 24-hour accounting window and are removed on the next successful run. Expired refresh/account tokens and rate rows are purged too.

Saved material persists until deletion; no raw original source is saved by default. Email addresses/password hashes are account data. Backups and platform logs have independent retention: choose and publish a concrete policy (for example 30-day encrypted backups), storage region, access controls, support contact and incident/deletion procedure. Do not publish an example retention period as if configured. Update the in-app privacy page with your actual details before launch.

Use managed PostgreSQL backups/PITR and export encrypted offsite copies according to your recovery objectives. `pg_dump --format=custom` and `pg_restore --no-owner --no-acl` can support independent backups/restores. Supply credentials through a protected environment or `.pgpass`, not committed scripts or command history. Never test restore against production. Restore to a separate database, run Alembic revision/schema checks, verify a sample account's saved sets in staging, and record recovery time/data loss. A backup command succeeding does not prove a restorable backup.

## Rollback and incidents

Record the release commit and prior images/configuration. Snapshot the database before migrations. On failure, stop new generation, retain evidence without notes/tokens, and redeploy compatible prior application images; use a reviewed forward migration for schema repair. Do not run `alembic downgrade` blindly against live data. Restore a snapshot into a separate verified database when rollback requires it; estimate data loss before switching traffic. Rotate `SECRET_KEY` after a suspected compromise and delete active auth sessions; key rotation also invalidates access JWTs. Revoke provider/SMTP/proxy secrets separately when needed.

Set alerts for 5xx, health failures, SMTP delivery failures, provider spend, rejected quotas, cleanup failures, database capacity/connection exhaustion and backup age. Establish on-call/support ownership. Rate limits are abuse controls, not full DDoS protection; use the hosting edge for connection and slow-upload protection.
