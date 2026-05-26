# Ex9 — Reflection


## Q1 — Planner handoff decision

## Your answer

In session `sess_426ffd7ac7ab`, the planner's first handoff decision is visible in the trace at `2026-05-26T01:57:19`. After producing 3 subgoals for the task "book for party of 12 in Haymarket", the executor called `handoff_to_structured` with:

```json
{
  "reason": "Request date confirmation",
  "context": "Party date not provided in task. Please specify a date for the event.",
  "data": {}
}
```

The signal that caused the decision was a missing required field — the planner determined it could not proceed with venue research without a confirmed date, so it handed off to the structured half to resolve the constraint. This is visible in the `session.state_changed` event immediately after: `from: loop → to: structured, round: 1`. The structured half then rejected with `normalisation failed: missing venue_id`, triggering the reverse handoff back to the loop.

**Citations:**
- `sessions/sess_426ffd7ac7ab/logs/trace.jsonl` — `executor.tool_called` `handoff_to_structured` at `2026-05-26T01:57:19`
- `sessions/sess_426ffd7ac7ab/logs/trace.jsonl` — `session.state_changed` `loop→structured` round 1

---
# Ex9 — Reflection

## Q2 — Dataflow integrity check

## Your answer

In ex5, the FakeLLMClient scripted `generate_flyer` with `total_gbp: 540`. The `calculate_cost` tool independently computed and logged `total_gbp: 540` into `_TOOL_CALL_LOG`. The integrity check called `fact_appears_in_log("£540")` and found the match — passing correctly.

A concrete scenario where it would catch a failure a human reviewer would miss: suppose the LLM calls `calculate_cost` for `haymarket_tap` with `party_size=6` (returning `£540`), but then hallucinates `total_gbp: 9999` in the `generate_flyer` call, perhaps because it misread a different venue's cost from earlier context. The flyer would contain `£9999`. A human reviewer skimming the flyer would see a plausible-looking pound amount and might not cross-check it against the tool output. The integrity check would call `fact_appears_in_log("£9999")`, find no matching tool output, and fail with `unverified_facts: ["£9999"]` — catching the fabrication automatically.

**Citations:**
- `starter/edinburgh_research/integrity.py` — `verify_dataflow`, `fact_appears_in_log`
- `sessions/sess_426ffd7ac7ab/logs/trace.jsonl` — `executor.tool_called` `generate_flyer`

---
# Ex9 — Reflection

## Q3 — First production failure and which primitive surfaces it

## Your answer

The first production failure I would expect is a missing required field in the handoff payload — exactly what happened in `sess_426ffd7ac7ab`. The loop half handed off to the structured half without a `venue_id`, causing the validator to reject with `normalisation failed: missing venue_id` across all three rounds, exhausting `max_rounds` without resolution.

The primitive that surfaces this is the **ticket state machine**. Each planner and executor action is wrapped in a ticket that transitions through `pending → running → success/failure`. When the executor calls `handoff_to_structured` with an incomplete payload, the ticket records the tool call arguments verbatim. The bridge reads the rejection reason from the structured half's response and writes a `session.state_changed` event with `rejection_reason: "normalisation failed: missing venue_id"`. In production, monitoring the ticket failure rate on `handoff_to_structured` tickets would immediately surface this pattern — a spike in rejections with the same `rejection_reason` string would identify the missing field as a systematic prompt or schema issue, not a one-off.

**Citations:**
- `sessions/sess_426ffd7ac7ab/logs/trace.jsonl` — `session.state_changed` `rejection_reason: "normalisation failed: missing venue_id"` rounds 1–3
- `starter/handoff_bridge/bridge.py` — `max_rounds` exhausted after 3 failed handoffs