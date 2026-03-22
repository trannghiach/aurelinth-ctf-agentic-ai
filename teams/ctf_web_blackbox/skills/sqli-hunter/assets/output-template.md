# SQLi Hunter Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Endpoint: [URL + method]
- Param: [injectable param name]
- DB: [MySQL / sqlite / PostgreSQL / unknown]
- Injection type: [UNION-based / error-based / blind boolean / blind time-based]

CONFIRMATION:
- Tool: [sqlmap / manual curl]
- Error/signal: [exact error text or blind true/false difference observed]

ENUMERATION:
- Databases: [list]
- Tables: [list]
- Columns: [list]
- Data: [flag value or extracted data]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
