# Ex6 — Rasa structured half

## Your answer

`RasaStructuredHalf` subclasses `StructuredHalf` and routes booking intent to Rasa via HTTP POST to `/webhooks/rest/webhook`. The input payload is normalised by `normalise_booking_payload` in `validator.py` before sending — this canonicalises currency strings (strips £, converts to int), date formats, party size, and venue_id.

The `sender_id` sent to Rasa is a hash of `(venue_id + date + time)` making it stable across retries within one session. Rasa's response is parsed for committed or rejected custom slots and returned as a `HalfResult`.

For offline mode a stdlib `ThreadingHTTPServer` mock is spawned that always confirms, allowing the HTTP contract to be tested without a real Rasa container. Network errors return `success=False` with `SA_EXT_SERVICE_UNAVAILABLE` rather than raising, so the bridge can decide whether to retry.

## Citations

- `starter/rasa_half/structured_half.py` — `RasaStructuredHalf.run`, mock server
- `starter/rasa_half/validator.py` — `normalise_booking_payload`