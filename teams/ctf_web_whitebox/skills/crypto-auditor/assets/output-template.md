# Crypto Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Weakness type: [predictable token / hardcoded secret / ECB / CBC bitflip / padding oracle / JWT confusion / hash extension / custom crypto]
- Source file: [FILE:LINE of crypto implementation]
- Key/secret: [value if hardcoded, or "server-held" if unknown]
- What forged token grants: [admin access / flag reveal / etc.]

CONFIRMATION:
- Isolation test: [CONFIRMED — describe the mathematical result / FAILED]
- Forge strategy: [description of the technique used]

EXPLOITATION:
- Forged credential: [token snippet or cookie value]
- Tested endpoint: [URL]
- Local test: [PASS / FAIL — response snippet]
- Real target: [PASS / FAIL]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
