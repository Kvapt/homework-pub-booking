# Ex7 — Handoff bridge

## Your answer

`HandoffBridge` in `starter/handoff_bridge/bridge.py` orchestrates round-trips between `LoopHalf` and `RasaStructuredHalf`. Each round runs the loop half; if `next_action=handoff_to_structured` the bridge invokes the structured half. If structured confirms, the session completes. If it rejects, the bridge builds a reverse task containing the `rejection_reason` and hands back to the loop for another attempt, up to `max_rounds=3`.

Every half transition emits a `session.state_changed` trace event recording `from`, `to`, `round`, and optionally `rejection_reason`. In session `sess_426ffd7ac7ab`, the structured half rejected in rounds 1 and 2 with `normalisation failed: missing venue_id`, visible in the trace as consecutive `structured→loop` state changes. The bridge exhausted `max_rounds` without resolution.

The offline scripted demo hardcodes the two-round trajectory: round 1 finds `haymarket_tap` (8 seats, rejected for party>8), round 2 finds `royal_oak` (16 seats, confirmed).

## Citations

- `starter/handoff_bridge/bridge.py` — `HandoffBridge.run`
- `sessions/sess_426ffd7ac7ab/logs/trace.jsonl` — `session.state_changed` events rounds 1–3