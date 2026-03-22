# Auth Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Auth mechanism: [Flask session / JWT HS256 / JWT RS256 / custom token / role from input]
- Weakness: [description + FILE:LINE, e.g. "Hardcoded SECRET_KEY = 'dev' — config.py line 3"]
- Bypass type: [session forgery / JWT none alg / algorithm confusion / role injection / predictable token]

CONFIRMATION:
- Isolation test: [CONFIRMED / FAILED — e.g. "forged token generated successfully"]
- Forged credential: [token snippet (first 30 chars) or cookie value]

EXPLOITATION:
- Tested endpoint: [URL]
- HTTP response: [status code]
- Local test: [PASS / FAIL — describe response snippet]
- Real target: [PASS / FAIL]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
