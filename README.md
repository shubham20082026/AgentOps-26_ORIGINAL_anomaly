# ReRoute

**Agentic recovery of cancelled food pickups**  
Built by **Shubham Parmar**, team **ORIGINAL_anomaly**, for AgentOps 2026 at MIT Bengaluru.  
Business domain: **Transport**.

[Live demo](https://agentops2026sparmar.streamlit.app/)

## What it does

When a food pickup is cancelled, ReRoute investigates replacement drivers and recipients, checks capacity and delivery constraints, and proposes a feasible plan or escalates with evidence.

The LLM chooses investigation tools. Python checks feasibility. A dispatcher approves the exact plan version before capacity is reserved. Both simulated parties must accept before the booking becomes confirmed. Declines, expiry and changed availability trigger capacity release and replanning with fresh approval.

The original interface uses dark forest accents. All cancellations, travel, handling evidence and replies are synthetic.

## Run locally

Requires Python 3.11 or 3.12. From this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux, use `python3` and `.venv/bin/python`.

**Quick demo:** Start fresh demo, select Happy path, ingest the cancellation and run recovery investigation. Review and approve the proposal, reserve capacity, then apply the driver and recipient accepts. Other scenarios demonstrate safe escalation or recovery.

## API and login

Offline mode is a rule-based baseline and needs no API key. LLM mode requires a tool-capable model and provider credentials. Configure local credentials with `configure-api.bat`, or use Streamlit Secrets for hosting. See [CLOUD_SETUP.md](CLOUD_SETUP.md).

Optional single-dispatcher login protects the workspace when configured. Without login settings, the app is a public synthetic sandbox. Password setup and limitations: [LOGIN_SETUP.md](LOGIN_SETUP.md). There are no default credentials.

Do not commit API keys, passwords, `.private/`, `.env` files, hosted Secrets or local databases.

## Verified results

**70 automated tests passed** on 24 October 2026, covering the workflow, approvals, concurrency, persistence, model errors, login and the fresh-demo capacity-message regression.

Five trials per mode across six synthetic scenarios:

| Result | LLM | Rule-based baseline |
|---|---:|---:|
| Correct outcomes | 30/30 | 30/30 |
| Median investigation | 22.1 s | 0.18 s |
| Observed range | 14.1–36.5 s | 0.062–0.391 s |
| Correct outcomes under 30 s | 25/30 | 30/30 |

Each mode produced five proposals and 25 justified escalations. These are correct investigations, not 30 food rescues. LLM timing includes request pacing and excludes human approval and confirmations. No automatic retry or deterministic substitution was used. The baseline was faster; LLM superiority and consistent sub-30-second latency are not established.

A separate live LLM check passed decline-driven replanning, fresh approval and both-party confirmation with the deterministic investigator disabled. The benchmark predates the login and visual updates.

Evidence: [evaluation_report.json](evaluation_report.json), [llm_recovery_verification.json](llm_recovery_verification.json), [LLM_REPAIR.md](LLM_REPAIR.md). The earlier failed evaluation remains archived under `evaluation_history/`.

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Scope and limitations

This is a working sandbox MVP. It has no real maps, messages, authenticated external replies or delivery verification. Optional login supports one dispatcher account, not role-based access or tenant isolation. The database owner can alter the audit. Synthetic handling flags do not certify food safety.

Local SQLite survives normal server restarts. Streamlit Community Cloud rebuilds may replace local files, so durable production storage remains future work. Confirmed allocations remain consumed until an operational completion feature is added.

Modeled savings of **65 dispatcher-minutes per week** assume five cancellations and coordination falling from 15 to two minutes per case. Actual savings and food delivered require a pilot.

## Submission documentation

- [Governance and Responsible AI](governanceandresponsiblity.md)
- [MVP Readiness](MVPreadiness.md)
- [Originality and Innovation](originalityandinnovation.md)
- [Business Value](BUSINESS_VALUE.md)
- [Reusability](REUSABILITY.md)
- [Architecture](ARCHITECTURE.md)

Before submission, push the complete project, reboot the hosted app and compare its **Build and deployment** SHA with the final GitHub commit. Hosted parity requires verification.
