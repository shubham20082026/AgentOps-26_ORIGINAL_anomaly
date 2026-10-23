# Business value and ROI model

This model matches slide 10, **Value per cancelled pickup**, in `ReRoute-Working-App-Final.pptx`. It separates observed software behavior from operating assumptions and modeled outcomes. No pilot, money saved, food delivered or emissions avoided has been measured.

## Measured

- Historical matched Happy-path trial: deterministic investigation 0.062 seconds; live LLM 16.75 seconds. Human review, approval and replies were excluded.
- A different earlier LLM run took 51.281 seconds and escalated after shared capacity was consumed. It is not a matched repeat of the Happy-path trial.
- The repeated evaluation in `evaluation_report.json` records five attempts per mode per scenario across six scenarios. Inspect correctness and failures alongside latency; fast failures are not rescues.
- The synthetic fixture contains 24 boxes and a 14:30 deadline. This is test input, not observed food rescued.

## Assumed — exactly the slide's illustrative inputs

| Input | Assumption | Evidence needed in a pilot |
|---|---:|---|
| Manual phone coordination | 15 minutes per cancellation | Observe comparable dispatcher cases |
| Agent-assisted coordination including approval | 2 minutes per cancellation | Measure operator work and confirmation delays |
| Cancellation volume | 5 per week | Record actual incidents |
| Donation size | 24 boxes per cancellation | Use actual loads and handling constraints |

The 2-minute assumption is **not** derived from LLM response latency. A 16.75-second investigation does not establish end-to-end coordination time or saved staff time. Escalations can require more human work.

## Modeled — not measured impact

```text
Time difference per cancellation = 15 - 2 = 13 minutes
Potential weekly dispatcher time = 13 × 5 = 65 minutes (1.083 hours)
Donation volume kept in consideration = 5 × 24 = 120 boxes per week
```

“120 boxes kept in play” is exposure volume, **not** boxes delivered, saved, recovered or diverted from waste. Expected deliveries would additionally require a measured recovery probability and confirmation/delivery evidence. Incremental impact also requires a manual-control comparison.

### Sensitivity to the assisted-time assumption

| Assisted time per cancellation | Potential difference per cancellation | Potential weekly time difference |
|---:|---:|---:|
| 2 minutes | 13 minutes | 65 minutes |
| 5 minutes | 10 minutes | 50 minutes |
| 10 minutes | 5 minutes | 25 minutes |
| 15 minutes | 0 minutes | 0 minutes |

All rows use the assumed 15-minute manual case and five cancellations weekly. API failures, extra review or slow confirmations can remove or reverse the benefit.

## Financial ROI framework

No wage rate, API bill, hosting cost or implementation cost was measured, so a monetary ROI is not claimed.

```text
Gross weekly labor value = measured staff-hours saved × local fully loaded hourly cost
Net weekly value = gross labor value - API - hosting - support - amortized implementation cost
ROI = net weekly value / total weekly cost   (only when cost > 0)
```

Do not use modeled box volume as revenue. A pilot should measure time to confirmed booking, operator minutes, recovery rate against manual dispatch, actual delivery before recipient close, false/infeasible proposals, operating cost and escalation workload.
