# Security implementation and limits

Access JWTs use PyJWT with fixed HS256, required claims, audience/issuer checks, random IDs and a live database session check. The original public signing key is rejected. Passwords use passlib's bcrypt_sha256; legacy bcrypt hashes can be checked and upgraded. Password recovery/change revokes all sessions and outstanding account links. Account verification requires both the emailed token and the password chosen at registration, preventing activation of an attacker-pre-registered password.

The switch from python-jose is a critical dependency exception to the original architecture notes: the audit reported GHSA-3qf3-8w2g-rqmx with no patched python-jose release and a transitive ecdsa advisory. Our HS256-only configuration did not use asymmetric keys, but retaining the vulnerable dependency was unnecessary. React Router was updated from 6 to 7.18.5 for GHSA-wrjc-x8rr-h8h6 and GHSA-337j-9hxr-rhxg; the React 18 SPA and URL structure remain.

Refresh and CSRF cookies are HttpOnly, SameSite=Lax, root scoped, and Secure with `__Host-` names in production. CSRF values are returned through a same-origin response for explicit client headers. Authentication cookies are never the authorization source for private study-set operations. Origin, host, Fetch Metadata and body limits apply before routes. Cookies require the same-origin frontend `/api` proxy; direct cross-site deployment is intentionally unsupported.

SQL parameter binding, strict request/output schemas, owner-scoped queries, database constraints, provider timeouts and persistent SQL rate limits cover the principal API boundaries. A global PostgreSQL quota row serializes generation reservations across processes; per-user and total daily limits count failed attempts as well. Anonymous timestamp-only cost reservations survive account deletion so deleting/recreating accounts cannot reset the shared budget. Each reservation can call the provider up to twice, at 6,000 output tokens per attempt. These limits are not dollar budgets: configure provider spending limits and alerts too. Input characters do not guarantee a fixed token count or cost. Browser cancellation does not guarantee cancellation or refund at the provider.

The PDF parser runs in a short-lived isolated Python child with a scrubbed environment, CPU/address-space limits, a temporary directory and an enforced wall timeout. This is resource isolation, not a complete operating-system sandbox; a native parser vulnerability could still act as the container user. Keep the parser updated, retain container restrictions, and obtain a security review for untrusted upload exposure. Backend support is macOS/Linux and Linux containers.

Logs deliberately exclude notes, passwords, JWTs, email links and provider response bodies. Uvicorn access logs are disabled in deployment commands. Configure platform/edge logging, trace storage and APM to redact authorization/cookie/proxy headers and request bodies. Request IDs and exception class names support diagnosis without recording content. Scope SMTP/provider credentials minimally and rotate any credentials that have appeared in history.

## Dependency audit exception

As of 2026-10-31, one advisory remains in **development tooling only**: minimatch GHSA-g3hv-75wg-m249 (moderate glob denial of service), inherited by ESLint 9 and its React tooling. Their declared compatible dependencies have no audited patched path; forcing minimatch's incompatible major API underneath them is not a safe fix. These tools read repository-owned configuration and paths in isolated CI, and are excluded from runtime images (frontend image contains only static assets and Caddy). CI does not run privileged pull-request workflows or expose deployment secrets to lint jobs.

`scripts/audit-web.mjs` reports this exact advisory, requires every affected package instance to be a development dependency, and expires the exception on **2026-11-30**. Any other advisory, a runtime occurrence, an expired exception or an audit error fails the gate. `npm audit` still reports the tooling advisory; there is no claim of a clean full npm audit. The operator must accept this residual tooling risk explicitly in the release checklist or replace/update the lint toolchain before release. No Python advisories are allowlisted.

Report issues privately to the repository owner's security reporting channel. Before public launch, configure that channel and a monitored user support address, publish operator identity, hosting/provider details, retention and deletion timelines, and applicable policies. Do not submit sensitive examples in public issues.

Primary references:

- https://github.com/advisories/GHSA-3qf3-8w2g-rqmx
- https://github.com/advisories/GHSA-g3hv-75wg-m249
- https://pyjwt.readthedocs.io/en/stable/usage.html
- https://platform.claude.com/docs/en/docs/about-claude/model-deprecations
- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
