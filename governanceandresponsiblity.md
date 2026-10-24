# Governance and Responsible AI

ReRoute by **Shubham Parmar**, team **ORIGINAL_anomaly**. Status as of 24 October 2026: working synthetic sandbox with optional single-dispatcher login.

## Responsibility boundaries

The LLM investigates a cancelled pickup and proposes a replacement. Python checks feasibility. A human approves the exact plan version before capacity can be reserved. Both simulated parties must accept before the application reports a confirmed sandbox booking.

| Actor | Authority | Boundary |
|---|---|---|
| LLM investigator | Read case, inspect resources, validate pairs, propose, escalate | Cannot approve, reserve capacity, send replies or change evidence |
| Deterministic validation | Enforce capacity, availability, handling flags, deadline and receiving window | Relies on synthetic evidence, not real food-safety verification |
| Dispatcher | Review, approve or reject a version, initiate reservation and simulation controls | Public-mode names provide attribution only |
| Driver and recipient simulation | Accept, decline or time out | Replies do not authenticate real people or send messages |

Only tools whose prerequisites are met are advertised to the model. Execution enforces those requirements independently. Inputs must use known IDs and accepted arguments. Approval binds a case version and plan fingerprint. Changed evidence invalidates the previous approval.

## Security and access

Optional configured login gates the workspace, database access, evaluation and API actions. Passwords use salted PBKDF2-SHA256 hashes with 600,000 iterations. The application has no default credentials. Sessions expire after one hour, credential changes invalidate sessions, and sign-out clears session state. Five sign-in attempts per server process per minute are allowed. Partial configuration blocks access until corrected. See [LOGIN_SETUP.md](LOGIN_SETUP.md).

A signed-in approval uses the configured account name. This is **one dispatcher account**, not role-based access, individual multi-user identity, independent approval authority or tenant isolation. With no login configuration, the app remains an explicitly labeled public synthetic sandbox. Do not use it for sensitive operational data.

Provider keys come from environment variables, Streamlit Secrets or locally encrypted Windows DPAPI configuration. The application excludes private configuration, environment files and database files from Git. HTTPS-only API endpoints and refusal of redirects reduce accidental credential forwarding. Configure only trusted endpoints. See [SECURITY_CHECK.md](SECURITY_CHECK.md) for the recorded scan scope; this is not a guarantee about every possible historical or remote artifact.

## Privacy and explainability

Demo cases, resource identities, travel and replies are synthetic. The configured provider receives case information and tool results. Real donor, driver or recipient data requires a privacy review, a retention policy and appropriate provider arrangements before use.

The interface exposes constraint evidence, proposal details, failure reasons and an exportable SQLite audit. Provider failures use sanitized categories instead of logging raw provider error payloads. The audit is append-only through application operations, but a database owner can modify the file. It is not tamper-proof.

## Safe failure and recovery

- No feasible pair produces an explicit escalation after required checks.
- Provider, quota, network, protocol and budget failures stop for manual review.
- The app does not silently substitute deterministic results for failed LLM investigations.
- Declines, timeouts and expired holds release pending capacity.
- A revised proposal requires fresh human approval.
- Transactional checks and unique reservation keys prevent duplicate or competing allocations in the tested SQLite workflow.

The LLM loop is bounded to 18 rounds and 24 tool calls. A 180-second elapsed budget is checked between requests, with a 30-second request timeout. An in-flight request can extend elapsed time beyond that budget. These bounds are not a guaranteed 30-second recovery SLA.

## Evidence and remaining gaps

The latest local automated suite passed **70 tests**, including login, logout, expiry, partial-configuration blocking and throttling alongside workflow tests. Repeated live LLM results and a decline/replan check are documented in [MVPreadiness.md](MVPreadiness.md). These checks do not establish production security or operational reliability.

Before operational use, add an identity provider, server-side role authorization, authenticated external replies, protected durable audit storage, tenant isolation, retention controls and security testing. Community Cloud rebuilds may discard local SQLite files. Food-safety handling booleans require replacement with verified evidence.

Confirmed sandbox boxes are allocations, not proof of delivery, avoided waste or emissions reduction. See [ARCHITECTURE.md](ARCHITECTURE.md) for transaction and approval invariants.
