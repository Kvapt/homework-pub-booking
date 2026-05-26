# Ex5 — Edinburgh research loop scenario

## Your answer

I implemented four tools in `starter/edinburgh_research/tools.py`: `venue_search`, `get_weather`, `calculate_cost`, and `generate_flyer`. The first three read from JSON fixtures in `sample_data/` and are marked `parallel_safe=True`. `generate_flyer` writes `workspace/flyer.html` and is `parallel_safe=False`.

The offline run (`make ex5`) uses `FakeLLMClient` with a scripted two-subgoal trajectory. Subgoal 1 calls `venue_search`, `get_weather`, and `calculate_cost` in parallel. Subgoal 2 calls `generate_flyer`. The flyer uses `data-testid` attributes on every fact so `verify_dataflow` can extract them by structured parsing rather than loose regex.

The dataflow integrity check in `integrity.py` extracts money facts (£N), temperature facts, and weather conditions from the flyer, then calls `fact_appears_in_log` for each against `_TOOL_CALL_LOG`. Every tool call records its arguments and output into the log before returning. A fact that appears in the flyer but not in any tool output fails the check with `unverified_facts`.

## Citations

- `starter/edinburgh_research/tools.py` — all four tool implementations
- `starter/edinburgh_research/integrity.py` — `verify_dataflow`, `fact_appears_in_log`