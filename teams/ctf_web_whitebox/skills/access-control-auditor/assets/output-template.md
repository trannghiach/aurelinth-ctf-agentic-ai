# Access Control Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Weakness type: [IDOR / role check bypass / horizontal privesc / mass assignment / path-based bypass]
- Source file: [FILE:LINE of vulnerable query or handler]
- Missing check: [description of the absent validation, e.g. "AND user_id = session.user_id"]
- Target object: [what to access, e.g. "notes.id=1, admin's note containing FLAG"]
- Auth required: [YES — any valid session / NO]

CONFIRMATION:
- Isolation test: [CONFIRMED — query has no ownership constraint / FAILED]

EXPLOITATION:
- Tested endpoint: [URL]
- HTTP response: [status code]
- Local test: [PASS / FAIL — response snippet]
- Real target: [PASS / FAIL]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
