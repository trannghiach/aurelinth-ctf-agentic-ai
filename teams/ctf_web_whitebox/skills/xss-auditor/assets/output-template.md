# XSS Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Source file: [FILE:LINE of vulnerable output]
- Rendering context: [HTML body / HTML attribute / JS string / URL / DOM]
- Injection point: [route + parameter name]
- Sanitization: [escaping function present, or "none"]
- Admin bot: [YES / NO]
- CSP: [header value verbatim, or "none"]

CONFIRMATION:
- Isolation test: [CONFIRMED / FAILED / SKIPPED]
- Tool: [python3 isolation test / curl local / dalfox]
- Payload: [exact payload string used]
- Filter bypass: [technique used, or "None needed"]

ESCALATION:
- Method: [OOB HTTP / DNS exfil / in-app relay / double-bot / internal endpoint / not attempted]
- OOB URL: [interactsh URL used, or N/A]
- Result: [OOB_STATUS: RECEIVED with cookie/data snippet / OOB_STATUS: EMPTY / N/A]
- Data obtained: [cookie value, flag, or N/A]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
