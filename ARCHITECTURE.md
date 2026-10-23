# Architecture and safety contract

```text
Streamlit dispatcher dashboard
   ├─ Ingest synthetic cancellation → SQLite case v1 + audit
   ├─ Investigator (deterministic OR configured LLM)
   │    read_case → inspect resources → validate alternatives → propose / escalate
   ├─ Human review → approve exact version + fingerprint + actor
   └─ Reserve capacity → simulated replies → verify booking / release + escalate
```

## State transitions

`OPEN → PROPOSED → APPROVED → AWAITING_CONFIRMATIONS → CONFIRMED`

`OPEN / PROPOSED → ESCALATED` when no feasible option or model failure.

`AWAITING_CONFIRMATIONS → ESCALATED` on decline, timeout or TTL expiry; pending capacity is released. A declined/timed-out party becomes unavailable in the case evidence. A new investigation can select an alternative or escalate. Every new proposal increments the version and clears approval. Capacity edits increment version, clear proposal and approval, release pending holds, and return to OPEN. Confirmed cases cannot be edited in this sandbox.

## Agent permissions

The model receives exactly six tools: read case, inspect driver, inspect recipient, validate pair, propose and escalate. It cannot approve, reserve, respond to confirmations or modify evidence. It must read and inspect before validating, and validate successfully before proposing. Declaring no feasible option requires checking all resource pairs. Tool data is treated as data. Inputs are restricted to known resource IDs and string arguments; extra fields are rejected.

The deterministic controller inspects all resources, checks all pairs and proposes the earliest feasible arrival. Both controllers use the same tool implementation. The LLM controller allows 18 rounds, at most 24 tool calls, a 12-second request timeout and a 60-second elapsed budget checked between requests. A single in-flight request can extend the total beyond 60 seconds by up to its timeout; this is not a hard process deadline.

## Feasibility rules

- Full donation fits available driver and recipient capacity, after subtracting other HELD and CONFIRMED allocations.
- Driver available; recipient accepting.
- Both resources have positive handling evidence (`True`).
- Arrival = fixed pickup + synthetic travel minutes.
- Arrival is no later than the food deadline and inside the recipient's inclusive receiving window.
- No partial loads or splitting.

## Approval and transaction invariants

Every proposal includes a SHA-256 fingerprint over case ID, new version and checked plan. Approval binds the exact version and fingerprint. This is a local integrity binding, not a cryptographic signature or authenticated authorization system. Approval checks feasibility again. Reservation checks it again inside `BEGIN IMMEDIATE`, preventing concurrent check-then-write overbooking. Other active allocations are counted across cases sharing driver/recipient IDs. The synthetic fixture catalogue is the capacity source; a production version needs a canonical resource inventory and evidence revisions, rather than independent case snapshots.

`UNIQUE(case_id,version)` ensures repeated reservation commands return the same active allocation. Released/expired keys cannot be revived; a new version and approval are required. Reply updates and the final two-party check are atomic. Duplicate identical replies are harmless. Conflicting pending replies are rejected; terminal holds are immutable. Decline/timeout releases the hold and escalates. Confirmed capacity stays consumed until an operational delivery-completion feature is added.

Hold expiry is lazy: database reads/actions sweep expired reservations atomically. SQLite persists case state, resource evidence, plans, approvals, reservation status and an append-only application audit table. The local database owner can alter the file; the audit is not tamper-proof. Process failure rolls back an incomplete write. Restart resumes persisted pending reservations or expires them after their TTL.

## Source layout

- `app.py`: dashboard, dispatcher actions, simulation controls and evidence export.
- `reroute/engine.py`: validation and SQLite-backed transactional tools.
- `reroute/agent.py`: bounded model controller, deterministic controller, HTTP adapter.
- `reroute/fixtures.py`, `fixtures/*.json`: synthetic scenario definitions.
- `tests/`: engine, concurrency, failure, model protocol and UI tests.

## Responsible demo claims

Recovered-box metrics represent confirmed sandbox allocations only. They do not assert delivery or actual avoided waste. No real personal data, outbound messages or live integrations are used. Model access and real provider behavior must be validated separately with the user's provider credentials. The approval UI is a local dispatcher control, not production access control.
