# Two-account login verification — 24 October 2026

72 tests passed in 36.51 seconds. Both configured accounts sign in and approve using their own identity. Invalid or duplicate second-account configuration blocks access. Both accounts share dispatcher permissions and workspace data.

# Final submission check — 24 October 2026

**70 tests passed in 12.26 seconds** in the original forest-design project. This includes the complete Streamlit workflow, login/logout/expiry, failure handling, reservations and a regression verifying that the competing-booking hint appears only for actual other active allocations. Creator-credit and styling changes are included. No new live-provider benchmark was run during this final check. The 30/30 repeated LLM results below remain the recorded earlier experiment. Hosted commit parity is unverified.

Historical verification records follow.

---

# Repaired LLM path — 24 October 2026

Full automated suite: **65 passed in 32.53 seconds**. Tests cover legal action availability, evidence-bound terminal tools, batched inspections and validations, specific rejection feedback, protocol failures before partial execution, stale case evidence, pacing, categorized UI errors and absence of silent deterministic fallback.

Live repeated sample: 30/30 LLM attempts correct, 0 failures, 0 rejected calls. Median 22.1015 seconds; range 14.125–36.516; 25/30 correct under 30 seconds. Baseline: 30/30 correct, median 0.18 seconds. All five deterministic stress checks passed. Timing includes Gemini's 4.1-second per-process request interval, and excludes human approval/confirmation. This does not establish superiority or a universal latency guarantee.

Raw per-run traces, model responses and failure classifications are in evaluation_report.json. The pre-repair 1/30 report is retained under evaluation_history. The old 16.75-second and 51.281-second observations below are historical, not samples from the repaired distribution.

The repair has been verified locally against a real provider. Deployment still requires pushing the complete changes and rebooting Streamlit Cloud; no claim is made that the hosted site already runs this repair.

---

# Cached-module startup fix — 23 October 2026

Full suite: **55 passed in 10.83 seconds**. A regression test removes the optional build_revision helper from the already-loaded configuration module and verifies that the app still starts, ingests a case and produces a proposal. The revision display now degrades to a reboot message rather than blocking startup. Published config.py already contained the helper; rebooting Streamlit reloads cached modules. Push app.py and tests/test_ui.py together for the durable fix.
# Submission evidence update — 23 October 2026

Full suite: **54 passed in 33.55 seconds**. Two additional checks cover failure-aware latency summaries and safe checkout revision reporting. Historical 52-test results below remain valid for their earlier version.

Five trials per mode across six scenarios produced 60 attempts. The baseline was correct in 30/30. The LLM was correct in 1/30, with 29 failed investigations. Baseline median/range: 0.063 / 0.062–0.125 seconds. LLM all-attempt median/range: 0.438 / 0.375–17.172 seconds; the latter includes rapid failures and must not be presented as recovery latency. The one successful LLM attempt took 5.125 seconds. Per-scenario results and every trial are in evaluation_report.json.

A separate post-run No-capacity diagnostic returned HTTP 429 after rejected tool calls. Individual causes were not captured for the historical 29 failures. Future evaluations now capture sanitized failure details and avoid counting internal escalation events as model tool calls.

The historical 16.75-second Happy-path and 51.281-second escalated run are not part of this repeated distribution. There is no established LLM superiority or consistent under-30-second guarantee.

The live hosted app completed a new isolated deterministic Happy-path case (RR-212716C1, v2): approval, reservation and both simulated accepts resulted in Confirmed / 24 boxes. This verifies the current site's offline workflow; it does not verify the new commit is deployed. See RELEASE_CHECKLIST.md for pending GitHub sign-in/push and exact deployed-SHA checks.

---

# Cloud and evaluator update — 23 October 2026

- Full suite: 52 passed in 7.37 seconds, including the full Streamlit approval,
  reservation and both-confirmations workflow, fresh demos and evaluation UI.
- Previous interface-test stalls were traced to blocked sandbox loopback sockets;
  granting network access resolved the harness issue.
- Live matched Happy-path trial: baseline 0.062 seconds, 13 calls; LLM 16.75
  seconds, 8 calls. Both proposed correctly. One trial is not evidence of a
  consistent latency guarantee or comparative superiority.
- All five concurrency/recovery checks passed; see evaluation_report.json.
- Streamlit Secrets now supply hosted credentials; Windows DPAPI remains local.
- Hosted deployment is pending pushing these changes and configuring its Secrets.
- SQLite remains local-file storage; cloud rebuild durability is not guaranteed.

Historical notes below predate this update.
# Verification — updated 23 October 2026 (Asia/Kolkata)

## Latest verification — 23 October

- **40 backend/configuration tests passed in 2.91 seconds** in the installed
  project: `tests/test_workflow.py`, `tests/test_config.py`, and
  `tests/test_api_errors.py`.
- Tests cover Windows DPAPI encryption/decryption, environment overrides,
  endpoint validation, database paths independent of working directory,
  persisted bookings/approvals/audit in a fresh process, and credential-free
  actionable API errors, alongside the original workflow tests.
- Live tool calling succeeded with `gemini-3.5-flash-lite`. A complete LLM
  investigation completed in 51.281 seconds and correctly escalated because a
  previous confirmed 24-box booking exhausted capacity for another 24-box case.
  This exceeds the planned 30-second proposal target; no consistent LLM latency
  target is claimed.
- Other provider requests returned model-unavailable, busy or timeout errors.
  Live service availability and account quotas remain external dependencies.
- The latest full-suite attempt stalled during Streamlit interface testing and
  was stopped. The 40-test result excludes `tests/test_ui.py`; historical UI
  results below are not a fresh verification of the current version.
- GitHub Actions is configured to run these backend/configuration tests on
  Windows with Python 3.12. Hosted CI execution has not yet been verified.

## Historical verification — 22 October

The following results predate the encrypted configuration and API error changes.

Environment: Windows, Python 3.12.14, Streamlit 1.66.1, pytest 9.1.1. The complete tested dependency set is in `requirements-tested.txt`; `requirements.txt` pins the tested Streamlit release. Model/provider access was not available.

## Automated results

**31 tests passed in 4.87 seconds**, including:

- End-to-end Streamlit dispatcher flow: ingestion, investigation, approval gating, reservation, driver acceptance, recipient acceptance and confirmed-box metric.
- Streamlit stale-capacity flow: approval invalidation and escalation after B capacity drops to eight.
- Five infeasible fixture scenarios rejected with no allocation.
- Exact-version approval, fingerprint tampering, human rejection and revised-plan invalidation.
- Ten repeated reservation commands returning one allocation; concurrent duplicate commands returning one allocation.
- Two competing cases reserving concurrently: only one succeeds when capacity cannot support both.
- Decline/timeout from either party, hold release, expiry, restart, stale replies and conflicting pending replies.
- Failure recovery selects a different driver and requires fresh approval.
- Model tool protocol with mocked responses, bounded invalid calls, mocked timeout, HTTP request payload and secret-safe error audit.

The first full UI test attempt hit a 20-second initialization timeout; the subsequent final run with a 60-second harness budget passed all tests. Backend-only run separately passed 29 tests in 2.99 seconds. The test budget allows for cold machine initialization; it is not the measured proposal latency.

## Repeated deterministic rehearsal

`rehearsal_report.json` contains actual measured runs and a complete sample audit, generated by `python rehearse.py`:

| Check | Result |
|---|---|
| Happy-path proposal trials | 10 |
| Median proposal time, approval excluded | 0.053486 seconds |
| Maximum proposal time | 0.107316 seconds |
| Repeated reservation commands | 100 across 10 independent databases |
| Unique reservations | 10 |
| Duplicate reservations | 0 |
| Invalid scenarios | 5/5 rejected and escalated |
| Adaptive failure recovery | D3 decline → release → D2 proposal, fresh approval required |

These are local synthetic measurements, not live-provider latency, production throughput or field impact. Regenerate the report on your laptop before presenting; results vary by hardware.

## Visible browser verification

The Streamlit server was started on localhost. The Happy path was manually driven through the actual browser: investigation, exact-plan approval, reservation, driver accept and recipient accept. The UI showed **Confirmed**, both accepted replies and **24 boxes confirmed in sandbox**. A dashboard preview is included as `preview.png`.

## Unverified or intentionally simulated

- At the time of the historical run, API tests used mocked transport only. See the latest verification above for subsequent live tests. Each deployment still needs its own provider credentials and model validation.
- Driver/recipient replies, travel times, availability and handling evidence are synthetic.
- No real dispatch, SMS, route lookup, delivery, food saved or emissions claim.
- No authentication, distributed deployment, canonical live resource registry or food-safety certification. See ARCHITECTURE.md and README.md.

The original proposal's goals of a sub-30-second sandbox proposal, rejecting five invalid fixture categories and zero duplicate bookings across ten replays were met in the deterministic local rehearsal. LLM latency and real-world benefits remain unverified.




A separate live LLM recovery check also passed: D3 was proposed, its simulated driver declined, capacity was released, and the model proposed D2. Fresh human approval was required. Both parties then accepted and the case became CONFIRMED. The deterministic investigator was disabled during this check. See [llm_recovery_verification.json](llm_recovery_verification.json).
