# MVP Readiness

ReRoute by **Shubham Parmar**, team **ORIGINAL_anomaly**. Updated 24 October 2026.

## Current readiness

ReRoute implements a complete **synthetic cancelled-pickup recovery workflow** in the Transport domain. It is ready for a controlled hackathon demonstration after the final pushed revision, hosted configuration and provider connection are verified. It remains a sandbox MVP with production gaps.

## Implemented workflow

| Stage | Working behavior |
|---|---|
| Data ingestion | Create a versioned case from a synthetic cancellation |
| Investigation | LLM chooses evidence-dependent tools, or an operator explicitly selects the rule-based baseline |
| Validation | Check full-load capacity, availability, handling evidence, deadline and receiving window |
| Human approval | Bind approval to an exact version and plan fingerprint |
| Execution | Reserve shared sandbox capacity transactionally with a unique reservation key |
| Verification | Confirm only after both simulated parties accept |
| Recovery | Release failed holds, revise resource evidence, replan and require fresh approval |
| Reporting | Display case status, constraint evidence, audit and downloadable JSON |

The interface includes fresh demo controls, API connection checks, an evaluation lab, dark forest accents and optional configured dispatcher login. Configured login gates access and binds approvals to the signed-in account. No credentials means a public synthetic sandbox. See [LOGIN_SETUP.md](LOGIN_SETUP.md).

## Automated evidence

The latest local suite passed **72 tests in 36.51 seconds** after the login and capacity-message fixes. Coverage includes the full UI workflow, stale approvals, shared-capacity conflicts, duplicate commands, expiry, release, persistence, model protocol, safe errors and authentication gating. Later creator-credit edits changed display text only and passed syntax checks.

Five deterministic stress checks passed: four simultaneous cases competing for capacity, ten repeated reservation commands, expiry with an injected clock, capacity-change invalidation and decline-driven replanning. This is limited synthetic concurrency evidence, not a production load test.

## Repeated live LLM evaluation

Five trials per mode across six scenarios produced 60 investigations on identical synthetic inputs and isolated databases.

| Measure | LLM investigator | Rule-based baseline |
|---|---:|---:|
| Correct outcomes | 30/30 | 30/30 |
| Valid proposals | 5 | 5 |
| Justified escalations | 25 | 25 |
| Median investigation time | 22.1015 s | 0.18 s |
| Observed range | 14.125–36.516 s | 0.062–0.391 s |
| Correct outcomes under 30 seconds | 25/30 | 30/30 |

LLM timing includes 4.1-second Gemini request pacing. Human approval and confirmation time are excluded. No automatic retry or deterministic substitution was used. These are **30 correct investigations, not 30 rescued donations**. No consistent sub-30-second guarantee or LLM superiority is established.

A separate live check proposed D3, processed a simulated decline, released capacity and proposed D2. Fresh human approval and both accepts then produced CONFIRMED. The deterministic investigator was disabled during that check.

Evidence: [evaluation_report.json](evaluation_report.json), [llm_recovery_verification.json](llm_recovery_verification.json), [LLM_REPAIR.md](LLM_REPAIR.md). The archived earlier 1/30 run remains in [evaluation_history/pre-repair-2026-10-23.json](evaluation_history/pre-repair-2026-10-23.json). The benchmark predates the login and visual changes; those changes did not trigger new live trials.

## Persistence and deployment

Local SQLite survives normal server restarts and preserves cases, approvals, reservations and audit. It does not guarantee persistence across Streamlit Community Cloud replacement or redeployment. Production durability requires external persistent storage.

The repaired code and latest UI have been checked locally. A working hosted page alone does not prove it runs those changes. Push the complete folder, reboot Streamlit, verify its checkout SHA and test configured login and provider access. See [CLOUD_SETUP.md](CLOUD_SETUP.md) and [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## Five-minute demonstration

1. Start a fresh Happy-path demo and select configured LLM mode.
2. Ingest cancellation, run investigation and inspect the evidence.
3. Approve the exact plan, reserve capacity and apply both simulated accepts.
4. Show confirmed status and the audit export.
5. Use a separate fresh case to show a decline or capacity change, revised investigation and fresh approval requirement.

If the provider fails, show the actual failure and manual escalation. An explicit baseline demonstration is available, but must be described as rule-based.

## Production gaps

Real maps, messaging, delivery verification, authenticated external replies, multi-user roles, tenant isolation, protected durable audit storage and operational allocation completion are outside this implementation. Synthetic handling flags do not certify food safety. ROI assumptions require dispatcher pilot data. See [BUSINESS_VALUE.md](BUSINESS_VALUE.md) and [governanceandresponsiblity.md](governanceandresponsiblity.md).

## Final submission checks

Before **24 October 2026, 6 PM IST**, complete development, commits, pushes, uploads and final saves. Submit the public secret-free repository, its full commit SHA, final PPT/PPTX and MP4 demo through the event portal. Keep the submitted source and artifacts frozen through judging. Portal completion, eligibility and final hosted commit parity still require team confirmation.

Event requirements: [AgentOps rules and judging](https://agentops.sdgmitblr.club/#judging), checked 24 October 2026.
