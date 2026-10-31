# Release approval

This implementation is not a launch certificate. CI must pass on the exact commit being deployed. Complete UAT and production checks before approving the release. No human approvals are supplied by this patch.

1. Apply/review the patch on a branch; confirm migrations against an empty database or produce an approved migration for existing data.
2. Run CI, including both Python versions, PostgreSQL, frontend unit/build/lint, dependency audits, container builds and Chromium/axe. Re-run failed infrastructure jobs; do not count missing browsers as successful tests.
3. Complete [QA-UAT.md](QA-UAT.md) with real SMTP and Anthropic, exact public domains, keyboard/screen-reader/mobile testing, security review, cost/abuse assessment and backup restore evidence.
4. Publish actual operator/support/privacy/retention information, configure monitoring, schedules, spending limits and an incident/rollback owner.
5. Review and explicitly accept the documented temporary development-tooling advisory, or eliminate it. Its audit exception expires on 2026-11-30; re-audit before deployment.
6. Copy `deploy/release.example.json` to `deploy/release.json`, fill the exact commit SHA, reviewers, date and evidence for each gate. Set a gate to approved only after observing its evidence. Do not include secrets or personal data in evidence files. Run `node scripts/check-release.mjs` at the release commit. The filled release record is ignored by Git to avoid a self-referencing commit SHA; retain it in your protected deployment record. Source changes must be committed and the working tree clean. Keep approvals/evidence in the release record; CI quality checks alone do not deploy or create sign-offs.
