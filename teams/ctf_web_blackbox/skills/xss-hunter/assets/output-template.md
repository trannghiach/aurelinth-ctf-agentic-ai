# XSS Hunter Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Endpoint: [URL + HTTP method]
- Injection point: [param name, rendering context, e.g. "POST param q, HTML body context"]
- Admin bot: [YES / NO]
- CSP: [header value verbatim, or "none"]

CONFIRMATION:
- Tool: [dalfox / manual curl / python3]
- Payload: [exact payload string used]
- Filter bypass: [technique used, or "None needed"]

ESCALATION:
- Method: [OOB HTTP / DNS exfil / in-app relay / double-bot / CSP-aware beacon / not attempted]
- OOB URL: [interactsh URL used, or N/A]
- Result: [OOB_STATUS: RECEIVED with cookie/data snippet / OOB_STATUS: EMPTY / N/A]
- Data obtained: [cookie value, flag, or N/A]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
