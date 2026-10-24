# ReRoute — a cancelled pickup deserves a second plan

AgentOps 2026 · 24 October 2026 · Team **ORIGINAL_anomaly** · **Shubham Parmar**

Domain: Transport / Retail and Supply. ReRoute recovers a cancelled food pickup using a bounded investigation loop, deterministic feasibility checks, human approval and verified sandbox bookings.

## Judging documents

- [Governance and Responsible AI](governanceandresponsiblity.md)
- [MVP Readiness](MVPreadiness.md)
- [Originality and Innovation](originalityandinnovation.md)

## Interface and dispatcher login

Dark forest accents now frame the workspace. Optional single-dispatcher login gates the entire app when configured. See [LOGIN_SETUP.md](LOGIN_SETUP.md) to generate a password hash and configure Streamlit Secrets. Without login configuration, the app remains a public synthetic sandbox. This does not implement RBAC or tenant isolation.

## Live demo

**[Launch ReRoute ↗](https://agentops2026sparmar.streamlit.app/)**

Try the food-pickup recovery workflow with synthetic scenarios, human approval, and sandbox booking confirmations.

> If the app is sleeping, click **“Yes, get this app back up!”** and wait for it to start.

**Status:** working hackathon sandbox prototype. The full investigation, approval,
reservation and both-party confirmation workflow is implemented. Driver and
recipient replies, travel times and availability are simulated. Real maps,
messaging, production role-based authorization and split deliveries are outside the current scope.

### Status and evidence

The complete sandbox workflow, fresh-demo controls, API connection check, evaluation lab, version-specific approval and both-party verification are implemented. The full suite now has **65 passing tests**, including LLM policy, batching, pacing and failure-display regressions. The working-app deck reports the earlier 52-test suite; its single-trial results are historical observations. Current validation is in [VERIFICATION.md](VERIFICATION.md).

The app still uses synthetic travel, resources, handling evidence and replies. There is no live delivery integration, production role-based authorization, donation splitting or guaranteed durable cloud database. LLM reliability is limited by provider/model behavior: see the repeated results below. GitHub Actions runs the full suite without live credentials.

## Repaired LLM evaluation — 24 October 2026

The model now receives tools whose prerequisites are met, exact resource IDs and actionable policy feedback. Independent checks may share a model response. **The LLM chooses investigation steps and proposals; the deterministic investigator is never used as its fallback.** See [LLM_REPAIR.md](LLM_REPAIR.md).

Five trials per mode across six scenarios: **60 attempts** with identical synthetic inputs and isolated databases. Gemini request starts were paced at 4.1 seconds within one process; this wait is included in latency. No automatic retries or deterministic substitution were used. Human approval and confirmations are excluded. Raw traces, failures and code hashes are in [evaluation_report.json](evaluation_report.json).

| Scenario | Mode | Correct | Failed | Median (s) | Range (s) |
|---|---|---:|---:|---:|---:|
| Happy path | deterministic | 5/5 | 0 | 0.188 | 0.062–0.391 |
| Happy path | llm | 5/5 | 0 | 16.171 | 14.125–23.391 |
| No capacity | deterministic | 5/5 | 0 | 0.188 | 0.063–0.203 |
| No capacity | llm | 5/5 | 0 | 20.375 | 17.437–20.812 |
| Late arrival | deterministic | 5/5 | 0 | 0.203 | 0.062–0.25 |
| Late arrival | llm | 5/5 | 0 | 24.203 | 20.453–25.25 |
| Missing handling | deterministic | 5/5 | 0 | 0.171 | 0.062–0.235 |
| Missing handling | llm | 5/5 | 0 | 31.922 | 24.109–36.516 |
| Closed recipient | deterministic | 5/5 | 0 | 0.063 | 0.063–0.219 |
| Closed recipient | llm | 5/5 | 0 | 28.094 | 24.672–36.125 |
| Driver unavailable | deterministic | 5/5 | 0 | 0.188 | 0.078–0.312 |
| Driver unavailable | llm | 5/5 | 0 | 15.875 | 15.609–17.438 |

**LLM: 30/30 correct; baseline: 30/30 correct.** LLM median **22.1015 seconds**, range **14.125–36.516 seconds**; baseline median **0.18 seconds**. 25/30 LLM attempts were correct and under 30 seconds. There were 0 failed LLM investigations and 0 rejected tool calls in this sample.

These trials validate the repaired synthetic workflow, not production reliability or superiority. The rule-based baseline remains much faster. No consistent sub-30-second guarantee is claimed.

The old **1/30** run is preserved in [evaluation_history/pre-repair-2026-10-23.json](evaluation_history/pre-repair-2026-10-23.json). It exposed invalid tool-call loops and provider failures, with incomplete per-trial diagnostics. Historical 16.75-second and 51.281-second runs used the earlier controller and are not included in this new distribution. The repair changes tool availability, feedback and request pacing; it does not simply relabel old failures as successes.

To reproduce locally (uses provider quota):

```powershell
.\.venv\Scripts\python.exe evaluate.py --repeats 5 --include-llm --output evaluation_report.json
```

Omit `--include-llm` for the baseline. Provider quotas, load and model access still apply.



A separate live LLM recovery check also passed: D3 was proposed, its simulated driver declined, capacity was released, and the model proposed D2. Fresh human approval was required. Both parties then accepted and the case became CONFIRMED. The deterministic investigator was disabled during this check. See [llm_recovery_verification.json](llm_recovery_verification.json).

## Business value

See [BUSINESS_VALUE.md](BUSINESS_VALUE.md) for the slide-aligned **measured / assumed / modeled** split. With assumed 15-minute manual coordination, 2-minute assisted coordination and five weekly cancellations, potential time difference is **65 minutes/week**. The **120 boxes/week** represents donation volume kept in consideration, not food delivered or saved. No financial ROI or field benefit is measured.

## Reusability

[REUSABILITY.md](REUSABILITY.md) maps fixtures, tools, deterministic checks, approver roles, reservation adapters and audit storage to their implementation points. Hospitality, supply and IT examples are future adaptations requiring new domain validation.

## Responsible AI and governance

The model investigates and proposes; it cannot approve, reserve or confirm. Deterministic checks enforce feasibility, approvals bind an exact version and fingerprint, failed holds release capacity, and the audit records evidence and failure reasons. Provider errors stop for manual review; fallback is an explicit operator choice. See [ARCHITECTURE.md](ARCHITECTURE.md).

**Roles gap:** optional configured login authenticates one dispatcher account and binds approvals to it. Public-mode names remain attribution only. Neither mode provides roles or separate approval authority. The hosted sandbox has no tenant isolation or production RBAC; its database owner can edit the audit. Before operational use, add authenticated dispatcher/reviewer/admin roles, server-side permission checks, separation of approval authority, protected durable audit storage, authenticated replies, retention controls and access-control tests. Do not submit personal recipient data to this public demo.

## Deployment and source version

[CLOUD_SETUP.md](CLOUD_SETUP.md) covers hosted Secrets, fresh demos and limitations. The new **Build and deployment** sidebar shows the checkout commit. Before the freeze, compare that full hash with GitHub's final pushed commit. A healthy page or matching button labels alone does not prove commit parity. [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) records what has and has not been verified.

Windows-encrypted credentials stay on your laptop; configure the hosted API in Streamlit Secrets. `.private/`, `.env*`, local databases and environments are gitignored. See [SECURITY_CHECK.md](SECURITY_CHECK.md) for the history-scan scope.

## Start here (Windows, beginner friendly)

1. Install Python 3.11 or 3.12 from https://www.python.org/downloads/ and select **Add Python to PATH**.
2. Extract this ZIP. Open the extracted `ReRoute` folder. Click the address bar, type `powershell`, press Enter.
3. Run each line below, waiting for it to finish:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

4. Open http://localhost:8501 if the browser does not open automatically.
5. Select **Happy path**, click **Ingest cancellation**, then **Run recovery investigation**.
6. Review the proposal. Enter your dispatcher name, tick the review checkbox, and click **Approve this version**.
7. Click **Reserve approved capacity**. Apply the driver's accept reply and then the recipient's accept reply. Only now does the case become Confirmed.

No API key is needed. No terminal activation or execution-policy change is required. Keep the terminal open; Ctrl+C stops the server. Linux/macOS: use `python3 -m venv .venv`, then `.venv/bin/python` in place of the Windows interpreter path.

Run the repeatable tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Core tests use temporary SQLite files and never modify demo data. `tests/test_ui.py` also exercises the Streamlit workflow.

## Optional real LLM tool selection

### Secure Windows setup (recommended)

Double-click `configure-api.bat`. Enter your provider's HTTPS Chat Completions
endpoint, a tool-capable model ID, and your API key at the hidden prompt. The key
is encrypted with Windows DPAPI for the current Windows user and saved in
`.private/api.dpapi`, which is excluded from Git. No plaintext key is written to
the project, database, exports, or setup log. Do not paste your key into chat.
Restart with `launch.bat`, then select **LLM · configured API**. The sidebar reports
whether configuration is present; it does not claim the provider has accepted it.
Run setup again to replace the credentials. A different Windows account or machine
must run setup again. Software running as your Windows user can decrypt the saved
key. The application refuses API redirects to avoid forwarding credentials.

Existing environment-variable configuration remains supported and takes priority.
When supplying an environment key, also supply its model and optional endpoint;
saved credentials are not mixed with environment credentials. Only use provider
endpoints you trust, since that endpoint receives the API key and case data.

Set environment variables in the same terminal before starting Streamlit:

```powershell
$env:REROUTE_API_KEY = 'your-provider-key'
$env:REROUTE_MODEL = 'your-tool-capable-model-id'
$env:REROUTE_API_URL = 'https://api.openai.com/v1/chat/completions'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then select **LLM · configured API** in the sidebar. `OPENAI_API_KEY` is also supported. Use a model enabled for your account with Chat Completions function calling. Model name is intentionally configurable; no account access is assumed. The adapter uses HTTPS and Python's standard HTTP client, avoiding an SDK dependency. API keys are loaded from environment variables or the encrypted local configuration and are not stored in SQLite or exports. Do not commit secrets. `.env` files are not loaded automatically.

The endpoint receives synthetic case information and tool results. Live Gemini tool calling and one complete investigation were verified locally; automated protocol tests mock model responses. Provider failure, malformed calls or limits cause manual-review escalation; an operator can explicitly rerun in deterministic mode. Automatic silent model fallback is deliberately avoided so the UI cannot imply a model succeeded when it did not.

API implementation reference: [official OpenAI function-calling documentation](https://developers.openai.com/api/docs/guides/function-calling).

## Working versus simulated

**Working:** investigation tool loop, deterministic validation, plan fingerprints, versioned approvals, transactional shared-capacity holds, unique reservation keys, both-party confirmation gating, idempotent replays, expiration/release, recovery after rejection, SQLite audit, evidence export, dashboard and tests.

**Synthetic:** cancellations, availability, driver/recipient capacities, handling booleans, fixed travel durations, donor and recipient identities, replies. A confirmed sandbox booking is not proof of actual delivery, meals saved, emission reductions or food-safety compliance. There is no live map, SMS, NGO or fleet integration.

**Deterministic mode** is a rule-based tool controller, not an LLM. **LLM mode** actually permits the model to choose investigation tools; deterministic code still decides feasibility. Neither mode can approve itself.

## Demo data and persistence

The default database is always `<ReRoute project folder>/data/reroute.db`, even
when launched from another working directory. Relative `REROUTE_DB` paths are
also resolved against the project folder; absolute paths are used as specified.
The sidebar explains local storage limits; the Build and deployment section reports the checkout revision. Stopping and restarting the server
reopens this file without resetting cases, approvals, bookings or audit history.
An in-memory `REROUTE_DB` setting is rejected. Existing data is not migrated or
overwritten. If an earlier relative override created a file elsewhere, use its
absolute path to keep using that database. Do not run multiple computers against
a OneDrive-synchronized SQLite file. For hosted deployments, set `REROUTE_DB` to
a file on a persistent mounted volume; ephemeral hosting disks do not preserve
files after replacement or redeployment. For a backup, stop the server and copy
the database file to a safe location.

Eight scenarios are in `fixtures/` and generated by `reroute/fixtures.py`. State persists in `data/reroute.db` by default, including across app restarts. Override with `REROUTE_DB` to use another file. Each ingestion creates a new case ID. Resource IDs are shared across cases: confirmed bookings consume capacity. For a fresh demo session use a new database filename, e.g. `$env:REROUTE_DB='data/rehearsal2.db'`. This preserves the previous audit instead of deleting it.

Fixture times are frozen at 14:00; they are not today's current time. Reservation TTL uses actual elapsed wall time. Refresh the UI to process expired holds; every get/reserve/validation/confirmation operation also processes expiry. No background worker is needed for this local demo.

## Troubleshooting

- `py` not found: install Python, restart the terminal, or replace `py -3` with your Python executable path.
- `No module named streamlit`: use the exact `.venv` interpreter above and repeat dependency installation.
- Port busy: add `--server.port 8502` to the Streamlit command.
- No valid plan in Happy path: another case may already consume capacity; use a new database for rehearsal.
- Hold expired: investigate again, review the new version, approve and reserve again. Expired keys cannot be resurrected.
- No internet on event day: install requirements beforehand. Offline mode then needs no network.
- LLM mode fails: inspect the audit's error type, check credentials/model/network, or explicitly choose deterministic mode.

## Scope and next steps

This is a local single-dispatcher sandbox. Public-mode dispatcher names are attribution only. Configured login authenticates one dispatcher account. SQLite serializes writes; there is no distributed booking service. Handling flags stand in for verified real-world food-safety evidence. Travel times do not model traffic or loading. There is no splitting, live ingestion webhook, operational delivery-completion release, multi-user authentication and roles, cancellation of confirmed allocations or real messaging. These need production design and partner testing.

Built using the submitted `ReRoute[by ORIGINAL_anomaly]_final.pptx` 

