# Originality and Innovation

ReRoute by **Shubham Parmar**, team **ORIGINAL_anomaly**. Transport-domain prototype, 24 October 2026.

## The problem-specific contribution

ReRoute investigates a last-minute cancelled food pickup as a constrained recovery process. A replacement must carry the whole donation, meet handling requirements and reach an accepting recipient before the food deadline and receiving-window close. The process ends with a confirmed sandbox booking or an explained escalation.

Dispatch, resource matching and optimization are established approaches. ReRoute does not claim to invent them, nor to be the first food-rescue coordination system. Its contribution is the tested combination of evidence-dependent LLM investigation with strict execution and approval controls for this specific recovery scenario.

## What the implementation demonstrates

| Element | ReRoute implementation | Why it matters |
|---|---|---|
| Adaptive investigation | The LLM chooses inspection and validation steps from tools valid for the current evidence | Investigation order can respond to tool results instead of following only a fixed sequence |
| Actionable feedback | Rejected actions return progress and specific unmet prerequisites | The model can correct its next step without bypassing constraints |
| Batched checks | Independent inspections or validations can share a model response | Reduces avoidable model round trips while local execution remains controlled |
| Deterministic boundary | Python validates capacity, timing and handling requirements | Model output alone cannot authorize an allocation |
| Evidence-bound approval | Versions and plan fingerprints invalidate stale approvals | Revised plans require a new human decision |
| Recovery after failure | Declines release capacity, alter evidence and trigger a revised investigation | Demonstrates feedback-driven replanning rather than a one-shot recommendation |
| Outcome verification | Two simulated accepts gate confirmation | A proposal or reservation alone does not become a successful booking |

These are engineering contributions within this prototype. They are not claims that each individual technique is novel.

## LLM contribution versus the baseline

The baseline exhaustively checks pairs and chooses the earliest feasible arrival. The LLM chooses its investigation steps and proposes from validated evidence. Both use the same feasibility rules and approval boundary. There is no hidden automatic baseline fallback.

In five trials per mode across six synthetic scenarios, both achieved **30/30 correct outcomes**. Each produced five proposals and 25 justified escalations. LLM median investigation time was **22.1015 seconds**, versus **0.18 seconds** for the baseline. The LLM therefore showed **no measured speed or correctness advantage** in this small catalogue.

The live decline/replan check provides stronger evidence of agent behavior: D3 was proposed, declined in simulation, and the LLM subsequently proposed D2 with fresh approval before confirmation. The deterministic investigator was disabled for that check. This establishes working adaptive behavior, not superiority over conventional dispatch software.

See [evaluation_report.json](evaluation_report.json), [llm_recovery_verification.json](llm_recovery_verification.json) and [LLM_REPAIR.md](LLM_REPAIR.md). The historical 1/30 result remains archived so the controller improvement is reviewable rather than hidden.

## Differentiation that still needs validation

A larger resource catalogue, incomplete evidence or varied cancellation descriptions may make selective investigation more useful. That is a hypothesis. The current fixtures are small and structured, so exhaustive matching is cheap and effective.

A future comparison should hold constraints and scenarios constant, increase catalogue size, introduce controlled evidence changes, and measure correct outcomes, tool calls, provider cost, investigation latency and human review effort. Include an appropriate optimizer or stronger rule-based baseline. Count failures and escalations separately from successful proposals and completed deliveries.

## Reusability and boundaries

Fixtures, tools, constraints and approver responsibilities can change while the approval, reservation and audit pattern remains. Hospitality disruptions, replenishment failures and infrastructure recovery are possible adaptations, not implemented products. See [REUSABILITY.md](REUSABILITY.md).

All current travel, resource evidence and replies are synthetic. No real deliveries, financial ROI, avoided waste, emissions reduction or production safety are established. Governance and deployment gaps are documented in [governanceandresponsiblity.md](governanceandresponsiblity.md) and [MVPreadiness.md](MVPreadiness.md).
