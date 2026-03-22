# Deserialization Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Library: [pickle / PyYAML / jsonpickle / PHP unserialize / Java ObjectInputStream / node-serialize]
- Sink: [FILE:LINE of deserialization call]
- Delivery: [cookie name / POST param / file upload field / Redis key]
- Encoding: [raw bytes / base64 / URL-encoded]
- Flag location: [path found in docker-compose.yml or .env]

CONFIRMATION:
- Sink verified: [unsafe call confirmed at FILE:LINE]
- Gadget: [__reduce__ with subprocess.check_output / YAML apply / etc.]
- Local test: [PASS / FAIL — describe response snippet]

EXPLOITATION:
- Real target: [PASS / FAIL]
- Response snippet: [first 100 chars of flag-containing response]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
