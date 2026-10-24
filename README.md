# ReRoute

### Agentic recovery of cancelled food pickups

**Shubham Parmar · ORIGINAL_anomaly · AgentOps 2026 · MIT Bengaluru**  
**Business domain:** Transport

[Live application](https://agentops2026sparmar.streamlit.app/) · [Architecture](ARCHITECTURE.md) · [Evaluation results](evaluation_report.json)
Reviewer login credentials are provided privately in the project summary submitted through the AgentOps portal.

## Overview

I built ReRoute to address a specific coordination problem in food rescue: a volunteer cancels a pickup after the donation has already been packed. The dispatcher must find a replacement quickly, but a driver match alone is insufficient. The whole donation must fit, the driver must meet the handling requirements, and the recipient must be able to receive it before both the food deadline and its receiving window close.

ReRoute treats this as an investigation and recovery workflow. An LLM agent gathers evidence through tools and proposes a feasible replacement. Deterministic checks enforce the constraints, a human approves the exact plan, and the system confirms the sandbox booking only after both parties accept. If conditions change, the workflow releases pending capacity and supports a new investigation.

The current implementation is a working sandbox MVP. It demonstrates the complete coordination process with synthetic cases, resources, travel times and replies. It does not claim actual delivery or measured food-waste reduction.

## The business problem

A last-minute cancellation creates several decisions that must be resolved together:

- Which available driver can carry the entire donation?
- Which recipient can accept it within the required window?
- Does the available handling evidence satisfy the donation's requirements?
- Is the capacity still available when the dispatcher approves and reserves it?
- Have both parties accepted the replacement arrangement?

In the main demonstration, a pickup is cancelled at 14:00 and 24 packed boxes need delivery by 14:30. Recipient A has capacity for only eight boxes, so the system must reject that option for the full donation and investigate another feasible pairing. The objective is a checked, human-approved arrangement with an auditable outcome.

## How the workflow operates

1. **Ingest the cancellation.** Create a case with the donation, deadline, handling requirements and candidate resources.
2. **Investigate alternatives.** The LLM chooses tools to inspect driver and recipient evidence and validate candidate pairs.
3. **Propose or escalate.** A feasible pair becomes a proposal. If no valid option exists, the system records the reasons and escalates for human review.
4. **Review and approve.** The dispatcher reviews the evidence and approves the exact case version and plan fingerprint.
5. **Reserve capacity.** A transactional reservation rechecks availability and accounts for allocations shared across cases.
6. **Verify the outcome.** Both simulated parties must accept before the booking becomes confirmed.
7. **Recover from changes.** Declines, timeouts, expired holds or changed capacity release pending allocations and require replanning with fresh approval.

The interface includes a persistent case inbox, recovery workspace, constraint evidence, audit export, an evaluation lab and isolated fresh-demo controls.

## The agentic component

LLM mode uses a tool-capable model to select investigation steps from the current evidence. Its tool catalogue includes reading the case, inspecting drivers, inspecting recipients, validating pairs, proposing a plan and escalating.

The controller advertises actions whose prerequisites are met and enforces the same conditions again when executing a tool call. Independent checks can share a model response. Rejected actions return specific feedback so the agent can revise its next step. The investigation has explicit round, tool-call and time budgets.

The model cannot approve its own proposal, reserve capacity, change resource evidence or provide confirmation replies. Those responsibilities remain outside its tool permissions. Provider errors stop the investigation for review, and the application does not silently replace a failed LLM run with a deterministic result.

A separate **deterministic mode** exhaustively checks candidate pairs and selects the earliest feasible arrival. It provides a reproducible baseline and an explicit offline demonstration path. Both modes use the same feasibility and approval rules.

## Implementation

| Component | Implementation |
|---|---|
| Interface | Streamlit with a forest-green visual theme |
| Investigation | Bounded Python controller with LLM tool calling |
| Model access | Configurable HTTPS Chat Completions endpoint |
| Feasibility | Python checks for capacity, availability, handling evidence and arrival windows |
| State and audit | File-backed SQLite |
| Reservation consistency | Transactions, shared-capacity accounting and unique case/version keys |
| Human control | Approval bound to a case version and plan fingerprint |
| Optional access gate | Single-dispatcher login with salted password hashing and expiring sessions |
| Validation | Automated workflow, concurrency, model-protocol, login and Streamlit interface tests |

Version changes invalidate previous approval. Reservation commands are repeat-safe, and duplicate identical replies do not create additional bookings. Pending holds expire after 120 seconds. Confirmed allocations remain consumed until an operational completion workflow is implemented.

See [ARCHITECTURE.md](ARCHITECTURE.md) for state transitions, constraints and transaction invariants.

## Evaluation and results

The latest local automated suite passed **70 tests** on 24 October 2026. Coverage includes the complete interface workflow, stale approvals, competing reservations, repeated commands, expiry, persistence, model failure handling, login and the capacity-message regression.

For live investigation evaluation, I ran five trials per mode across six synthetic scenarios using identical inputs and isolated databases: **60 investigations in total**.

| Measure | LLM investigator | Deterministic baseline |
|---|---:|---:|
| Correct outcomes | 30/30 | 30/30 |
| Feasible proposals | 5 | 5 |
| Justified escalations | 25 | 25 |
| Median investigation time | 22.1 s | 0.18 s |
| Observed range | 14.1–36.5 s | 0.062–0.391 s |
| Correct outcomes under 30 seconds | 25/30 | 30/30 |

The six scenarios cover Happy path, No capacity, Late arrival, Missing handling, Closed recipient and Driver unavailable. Correctness includes rejecting infeasible arrangements. The results therefore represent **30 correct investigations per mode**, not 30 successful food rescues.

LLM timing includes a 4.1-second minimum request-start interval for Gemini within one server process. Human approval and confirmation time are excluded. No automatic retries or deterministic substitution were used. The baseline was faster, and this experiment does not establish LLM superiority or a consistent sub-30-second guarantee.

A separate live LLM recovery check also passed: the agent proposed D3, processed a simulated decline, released the hold and proposed D2. Fresh human approval and both accepts then produced a confirmed sandbox booking. The deterministic investigator was disabled during that check.

The earlier unsuccessful evaluation is retained for transparency. The repaired benchmark predates the later login and visual changes; it was not rerun as part of those interface updates.

- [Repeated evaluation and traces](evaluation_report.json)
- [Live decline and replanning evidence](llm_recovery_verification.json)
- [Controller repair and analysis](LLM_REPAIR.md)
- [Archived earlier evaluation](evaluation_history/pre-repair-2026-10-23.json)
- [Verification history](VERIFICATION.md)

## Business value

ReRoute aims to reduce the coordination effort needed to recover a cancelled pickup while making the decision and approval process easier to inspect.

The current business model assumes 15 minutes of manual coordination per cancellation, two minutes of assisted coordination including approval, and five cancellations each week. Under those assumptions, the potential difference is **65 dispatcher-minutes per week**. At 24 boxes per cancellation, **120 boxes per week** would remain under consideration for recovery. This is modeled volume, not measured food delivered or saved.

A pilot would measure actual dispatcher effort, time to confirmed booking, recovery rate and deliveries completed before the deadline. No financial ROI or field benefit has been measured. See [BUSINESS_VALUE.md](BUSINESS_VALUE.md).

## Responsible AI and governance

The design separates model judgment from permission to act. Deterministic checks validate feasibility, a dispatcher approves the exact plan, and both-party confirmation gates the reported booking outcome. The audit records evidence, decisions and failures for review.

Optional configured login gates access to the workspace and uses the signed-in account for approval attribution. It supports one dispatcher account rather than role-based authorization or independent reviewer identities. Without login configuration, the application is an explicitly labeled public synthetic sandbox.

Provider credentials are supplied through environment variables, Streamlit Secrets or locally encrypted Windows configuration. Private configuration and local databases are excluded from Git. The provider receives the case information and tool results required for investigation. The public demo should contain synthetic data only.

The audit is append-only through application operations, but the database owner can modify the underlying file. Production use requires stronger identity, authorization, audit protection and data-retention controls. Details are in [governanceandresponsiblity.md](governanceandresponsiblity.md) and [LOGIN_SETUP.md](LOGIN_SETUP.md).

## Running locally

Requires Python 3.11 or 3.12. From the project folder on Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

### Demonstration

Select **Start fresh demo**, choose **Happy path**, and click **Ingest cancellation**. Run the recovery investigation, review and approve the proposal, reserve capacity, then apply the driver and recipient accepts. The case becomes Confirmed only after both replies.

Other scenarios intentionally test infeasibility or recovery. An escalation can be the correct outcome when no safe replacement exists. Provider failures display their own error reasons.

### API configuration

Deterministic mode works without an API key. LLM mode requires credentials for a model that supports tool calling through Chat Completions. On Windows, `configure-api.bat` stores local credentials encrypted for the current Windows user. Hosted deployments use Streamlit Secrets. See [CLOUD_SETUP.md](CLOUD_SETUP.md) for configuration instructions.

Optional dispatcher login is configured separately as described in [LOGIN_SETUP.md](LOGIN_SETUP.md). There are no default login credentials. Never commit API keys, passwords, private configuration or local databases.

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

### Persistence

The default database is `data/reroute.db`, resolved relative to the project folder. Normal server restarts reopen the same database. **Start fresh demo** creates an isolated database and preserves previous records.

Local-file persistence does not guarantee durability across Streamlit Community Cloud replacement or redeployment. Operational deployment requires persistent storage. The hosted checkout revision is available under **Build and deployment** for comparison with the source commit.

## Scope and future work

The current scope is one whole donation, one replacement driver and one recipient per case. Resource availability, handling evidence, travel and replies are synthetic. There is no live map, messaging service, authenticated external response or delivery verification. Synthetic handling flags do not certify food safety.

Next steps include authenticated individual roles, protected durable storage, real partner integrations, a canonical resource inventory and an operational delivery-completion workflow. Larger-catalogue evaluation should compare selective LLM investigation with appropriate rule-based and optimization baselines before making performance claims.

The recovery pattern can extend to other constrained coordination problems by replacing fixtures, tools, constraint checks and approver responsibilities. Those adaptations require their own domain validation. See [REUSABILITY.md](REUSABILITY.md).

## Further documentation

- [MVP Readiness](MVPreadiness.md)
- [Originality and Innovation](originalityandinnovation.md)
- [Governance and Responsible AI](governanceandresponsiblity.md)
- [Architecture](ARCHITECTURE.md)
- [Business Value](BUSINESS_VALUE.md)
- [Reusability](REUSABILITY.md)
