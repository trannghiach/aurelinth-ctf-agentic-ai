# SSTI Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Engine: [Jinja2 / Mako / Twig / Smarty / Freemarker — with source import line]
- Injection type: [Type A (direct render) / Type B (variable injection)]
- Entry point: [route + parameter name]
- Flag location: [path from docker-compose.yml or .env]

CONFIRMATION:
- Isolation test: [CONFIRMED / FAILED — e.g. "{{7*7}} → 49"]
- RCE test: [CONFIRMED — e.g. "uid=1000(app) output confirmed" / FAILED]

EXPLOITATION:
- Payload: [exact SSTI payload used]
- Local test: [PASS / FAIL — describe response snippet]
- Real target: [PASS / FAIL]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
