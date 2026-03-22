# Auth Bypasser Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Endpoint: [login URL or admin panel URL]
- Auth mechanism: [login form / JWT / session cookie / IDOR]

CONFIRMATION:
- Technique: [default creds / SQLi / JWT none alg / JWT weak secret / cookie manipulation / IDOR]
- Payload: [exact credential or payload used]

ESCALATION:
- Access gained: [role achieved, e.g. "admin" / "user"]
- Accessible endpoints: [list of endpoints now accessible]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
