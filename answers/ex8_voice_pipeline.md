# Ex8 — Voice pipeline

## Your answer

`voice_loop.py` implements two modes sharing identical trace output. Text mode reads from stdin and prints manager responses — no API keys needed. Voice mode uses Speechmatics for STT and Rime.ai for TTS.

Graceful degradation: if `SPEECHMATICS_KEY` is missing and `--voice` is passed, the loop falls back to text mode with a visible warning rather than crashing. If `RIME_API_KEY` is missing, STT runs but TTS is skipped and responses are printed.

Every utterance — both user input and manager response — is logged to the session trace with `voice.utterance_in` and `voice.utterance_out` event types including timestamp from `now_utc()`. This makes the trace identical regardless of which mode ran, so downstream grading doesn't need to know.

`ManagerPersona` in `manager_persona.py` wraps `OpenAICompatibleClient` pointed at `Llama-3.3-70B-Instruct` on Nebius. The system prompt establishes a gruff Edinburgh pub manager who accepts bookings under £300 deposit and ≤8 people, and declines otherwise with a specific reason.

## Citations

- `starter/voice_pipeline/voice_loop.py` — text/voice mode, trace events, graceful degradation
- `starter/voice_pipeline/manager_persona.py` — `ManagerPersona`, system prompt