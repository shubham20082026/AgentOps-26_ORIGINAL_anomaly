# Submission release checklist

Freeze: **24 October 2026, 18:00 IST** (confirmed by the user). This checklist is a factual record, not a claim that every release action is complete.

## Completed in the prepared checkout

- Synced with public `main` at `d02d03f95263c41bff5c3f02836221e7fe5ba5d8` before edits. The repeated measurements used code from `fe59dfe242f13fc88d67395293aa6ee94b49cc92`; the intervening public commit changed README/devcontainer files, not the controller.
- Ran five trials per mode across six scenarios (60 attempts) and saved raw results/traces in `evaluation_report.json`.
- Baseline: 30/30 correct. LLM: 1/30 correct, 29 investigation failures. The short overall LLM median includes failures and is not recovery time. A separate diagnostic returned HTTP 429; original failed runs lack individual cause details.
- Added the slide-aligned business model, reuse points, Responsible AI/roles gap and honest README status.
- Full suite: **54 passed in 33.55 seconds**, including UI, transaction invariants, failure-aware reporting and build revision checks.
- Verified the currently hosted app through a new isolated deterministic Happy-path case `RR-212716C1`: version 2, dispatcher approval, reservation, both simulated accepts, Confirmed, 24 boxes. This tests sandbox behavior, not actual delivery or live LLM reliability.
- Preserved local encrypted credentials and existing databases; neither belongs in a commit.

## Pending account/deployment actions

- GitHub description/topics/website are not applied: the available browser is signed out and no noninteractive GitHub credential was available. Exact values are in `REPOSITORY_METADATA.md`.
- The submission changes are not yet on public `main`. Commit/push from an authenticated checkout before the freeze.
- Exact deployed commit parity is **unverified**. The currently hosted app lacks the new revision display. After push and redeploy, open **Build and deployment** and compare its full hash against `git rev-parse HEAD` and GitHub's final commit. Do not infer parity from a healthy homepage.
- If needed, reboot the hosted app and repeat the offline end-to-end flow. Test the API separately only when provider quota is available.

## Before the freeze

1. Sign in to GitHub, apply repository metadata, and commit/push the prepared changes.
2. Confirm Actions is green and the live build reports the exact pushed SHA.
3. Recheck credentials and the evaluation report before any later commit. Never upload `.private`, `.env` or live SQLite data.
4. Record the final commit SHA and time locally. Make no repository or deployment changes after **18:00 IST on 24 October**.

The hosted app's local SQLite files may be replaced on cloud rebuild; a production durable database, authentication and role separation remain future work.
