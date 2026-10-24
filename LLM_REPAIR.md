# LLM investigation repair — 24 October 2026

## Failure mode addressed

The old controller advertised every tool at every step. It could offer escalation before the required checks, then respond with generic feedback. Live diagnostics showed repeated rejected calls and HTTP 429. The old 1/30 report did not capture all individual causes; not every failure can be attributed retrospectively.

## Repair

- Offer only tools whose prerequisites are met. Enforce those prerequisites again on execution.
- First read the case, then inspect known resources, then validate inspected pairs. Propose requires a valid pair; escalation requires exhausting all pairs.
- Let the model batch independent inspections or validations to reduce provider round trips. The model selects resources, checks and its proposed feasible pair.
- Return actionable policy feedback and progress; stop after three consecutive rejections.
- Reject malformed call batches before any partial execution.
- Distinguish quota/provider, network, protocol, policy, stale evidence, configuration and budget failures. Do not log provider bodies or credentials.
- Pace Gemini requests with a 4.1-second minimum interval within one process by default. Configure REROUTE_MIN_REQUEST_INTERVAL from 0 to 30 seconds for the provider account. Latency includes pacing. This is not a distributed limiter or quota guarantee, and failed requests are not automatically retried.

The model cannot approve, reserve or confirm. LLM mode never invokes the deterministic investigator as fallback. Bounds remain 18 model rounds, 24 calls, a 180-second budget checked between rounds, and 30-second HTTP timeout.

## Evidence

The repair tests cover legal-action gating, batching, policy-feedback recovery, failure categories, malformed responses, stale evidence and pacing. A test disables the deterministic investigator and verifies that the LLM transport can choose a different valid pair than the baseline.

The new evaluation_report.json holds repeated live trials. evaluation_history/pre-repair-2026-10-23.json preserves the original report. Correctness and latency must be read together; rapid errors are not successful recoveries. No real delivery or production reliability is claimed.

## Deployment

Push all changed Python files and tests together, then reboot Streamlit Cloud to reload its modules. Compare the deployed checkout hash with the pushed commit. Select LLM mode and start a fresh demo for rehearsal. Keep local credentials and databases out of Git.

Protocol references:
https://ai.google.dev/gemini-api/docs/function-calling
https://ai.google.dev/gemini-api/docs/openai


A separate live LLM recovery check also passed: D3 was proposed, its simulated driver declined, capacity was released, and the model proposed D2. Fresh human approval was required. Both parties then accepted and the case became CONFIRMED. The deterministic investigator was disabled during this check. See [llm_recovery_verification.json](llm_recovery_verification.json).
