# Crypto Hunter Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Token type: [JWT / JWE / Flask session / Custom]
- Found at: [Cookie name or Authorization header, and endpoint where observed]
- Algorithm: [alg field value from header]
- Key material: [public key path / JWKS URL / none found]

CONFIRMATION:
- Tool: [jwt_tool / flask-unsign / python3]
- Attack: [algorithm confusion / weak secret / none alg / key forge / predictable token / etc.]
- Forged claim: [e.g. sub=admin, role=admin]
- Token accepted: [YES at /endpoint with HTTP 200 / NO]

ESCALATION:
- Tested endpoint: [URL]
- HTTP response: [status code]
- Response content: [relevant snippet verbatim from tool output]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
