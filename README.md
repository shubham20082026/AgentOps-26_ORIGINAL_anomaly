# ReRoute — a cancelled pickup deserves a second plan

AgentOps 2026 · 24 October 2026 · Team **ORIGINAL_anomaly** · **Shubham Parmar**

Domain: Transport / Retail and Supply. ReRoute recovers a cancelled food pickup using a bounded investigation loop, deterministic feasibility checks, human approval and verified sandbox bookings.

## Live demo

**[Launch ReRoute ↗](https://agentops2026sparmar.streamlit.app/)**

Try the food-pickup recovery workflow with synthetic scenarios, human approval, and sandbox booking confirmations.

> If the app is sleeping, click **“Yes, get this app back up!”** and wait for it to start.

**Status:** working hackathon sandbox prototype. The full investigation, approval,
reservation and both-party confirmation workflow is implemented. Driver and
recipient replies, travel times and availability are simulated. Real maps,
messaging, authentication and split deliveries are outside the current scope.

### Verification at a glance

- 52 tests, including interface checks, passed locally on 23 October 2026.
- A live Gemini tool-calling test and a complete LLM investigation succeeded.
- That investigation correctly escalated when an existing confirmed booking left
  insufficient shared capacity. Model availability and latency can vary.
- Full interface tests now pass; see the cloud update in VERIFICATION.md.

GitHub Actions runs the full test suite without provider credentials; it does not call a live model.

## Cloud deployment and evaluator improvements

See [CLOUD_SETUP.md](CLOUD_SETUP.md) for Streamlit Secrets and deployment steps.
Windows-encrypted laptop credentials are not transferred to the hosted app.

- Start fresh demo isolates capacity without deleting previous cases.
- Test API connection checks provider tool calling before a full investigation.
- Escalations show their recorded cause and investigation evidence.
- Evaluation lab compares the exhaustive rule-based baseline and optional live
  LLM on identical inputs. It measures correctness, latency, tool calls, failures
  and the 30-second target, with downloadable traces.
- Stress checks cover concurrent cancellations, repeated bookings, delayed
  confirmations, changed capacity and adaptive replanning.

The full suite now passes: **52 tests**, including Streamlit UI checks.
One measured Happy-path trial: baseline **0.062 seconds / 13 tool calls**, LLM
**16.75 seconds / 8 calls**, both correct. All five stress checks passed.
This single trial does not establish consistent latency or LLM superiority.
See `evaluation_report.json` for evidence.

Cloud files can be replaced on rebuild; operational durability needs external storage.

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

## What to demonstrate

See **DEMO_SCRIPT.md** for the 4-minute judge walkthrough, failure demonstrations and questions. See **ARCHITECTURE.md** for state transitions, tool permissions and transaction guarantees. See **VERIFICATION.md** for measured local results and limitations.

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
The sidebar shows the active database path. Stopping and restarting the server
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

This is a local single-dispatcher sandbox. Dispatcher names are attribution, not authenticated identity. SQLite serializes writes; there is no distributed booking service. Handling flags stand in for verified real-world food-safety evidence. Travel times do not model traffic or loading. There is no splitting, live ingestion webhook, operational delivery-completion release, user authentication, cancellation of confirmed allocations or real messaging. These need production design and partner testing.

Built using the submitted `ReRoute[by ORIGINAL_anomaly]_final.pptx` 
