# SQLi Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Source file: [FILE:LINE of vulnerable query]
- DB engine: [sqlite3 / MySQL / PostgreSQL]
- Entry point: [route + parameter]
- Sanitization: [type cast / regex / ORM / none]
- Column count: [N — from source SELECT statement]

CONFIRMATION:
- Isolation test: [CONFIRMED / FAILED]
- Exploit type: [UNION-based / blind boolean / blind time-based]
- Payload: [exact payload string]

ENUMERATION:
- Tables accessed: [table names]
- Columns extracted: [column names]
- Data: [flag value or other extracted data snippet]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
