# Four-minute demonstration — ORIGINAL_anomaly

Presenter: Shubham Parmar · AgentOps 2026 · 24 October 2026

## Before judging

Install dependencies and run tests before leaving for the venue. Start a fresh rehearsal database, keep the terminal running, and open the app. Use deterministic mode unless you have verified your model and network. Keep `VERIFICATION.md` and an exported evidence JSON available. Do not put API keys on screen.

## 0:00–0:30 — the business failure

“The food is packed. The volunteer cancels. Replacing a driver alone does not prove the rescue will work. ReRoute checks who can carry all the food, who can receive it on time, and whether both parties accept the replacement.”

Show **Happy path** and ingest the cancellation: 24 boxes at 14:00, deadline 14:30.

## 0:30–1:20 — investigate, reject, revise

Run recovery investigation. Open **Evidence & constraints**. Show Recipient A can receive only eight boxes. Driver 1 is unavailable; Driver 3 has insufficient capacity. Show rejection reasons. Return to the proposed Driver 2 → Recipient B plan, arrival 14:22.

“The Python validator rejects infeasible choices. The deterministic controller uses the same tools as the optional model controller. In this run I am using [state the actual selected mode]. The tool trace is persisted, not a typed narrative of what an agent might do.”

## 1:20–2:10 — meaningful human approval

Point out reservation is unavailable before approval. Enter your name, review the constraints, check the checkbox, approve the version. Reserve capacity. Apply driver accept only: status remains awaiting confirmations. Apply recipient accept: show confirmed sandbox booking.

“Approval applies to this exact plan version. A reservation is not a completed recovery. Both simulated replies must accept. These are sandbox replies; no real driver or NGO was contacted.”

## 2:10–3:00 — show a failure, not just a happy path

Use a new database for this segment, or demonstrate stale capacity before completing the initial booking. Ingest Happy path, investigate and approve. Expand **Failure lab**, change B capacity to 8. The version changes and approval disappears. Run investigation again: all pairs fail and the case escalates.

“An old approval cannot book a changed plan. The correct outcome here is escalation with evidence, not an invented successful rescue.”

Alternative: use **Recovery with alternate** in a fresh database. Investigate, approve and reserve Driver 3. Apply the default driver decline. Show RELEASED hold. Investigate again: it switches to Driver 2, arriving at 14:22, with a new plan version and no approval. Approve and reserve again; explicitly set both simulated replies to accept. This demonstrates adaptation to failure and fresh human oversight. The standard Recipient declines scenario correctly has no remaining feasible recipient.

## 3:00–4:00 — evidence and value

Open Audit & export. Show approval, hold, replies, verification or failure events. Download case JSON. Explain repeat-safe booking keys and restart persistence. Show the test results, especially concurrent booking, stale approval and ten replays.

“Our value is a checked replacement plan or a clear reason to intervene. We have working local safeguards, not a claim of live food delivery. Next we would pilot with a partner, authenticate dispatchers and replace fixture evidence with verified resource and route services.”

## Judge questions

**Why agentic?** The model mode selects investigation tools, sees rejection evidence and revises its choice. The code enforces evidence before proposals. Deterministic mode is an honest offline controller, not described as an LLM. Action execution is the real local reservation/verification workflow behind human approval.

**What happens if the model goes down?** It stops and escalates. No booking occurs. The dispatcher can explicitly retry with deterministic mode.

**Why not automatically book the top match?** Capacity, timing and handling must pass; approval must match the current plan; confirmation can still fail. A ranked candidate is not a confirmed recovery.

**What is the impact?** The demo measures confirmed sandbox boxes and workflow correctness. Real food saved, time savings and emissions require a pilot. Do not claim those as measured results.

**Does it guarantee success?** No. It demonstrates the submitted process clearly and reliably; judging and competition outcomes cannot be guaranteed.
