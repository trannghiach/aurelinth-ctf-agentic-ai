# IDOR Hunter Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Endpoint: [URL]
- Type: [numeric IDOR / UUID prediction / horizontal privesc / vertical privesc / HTTP method bypass]

CONFIRMATION:
- Evidence: [what tool output showed, e.g. "id=1 returns admin profile with different data"]
- Request: [exact curl command or URL]

ESCALATION:
- Resource accessed: [URL of privileged resource]
- Data obtained: [relevant content snippet from tool output]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
