# Race Condition Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Race type: [TOCTOU / coupon reuse / file-based / token reuse / limit bypass]
- Source file: [FILE:LINE of check and act]
- Window size: [DB queries / variable assignment / sleep — estimated ms]
- Win condition: [what winning the race achieves]

CONFIRMATION:
- Isolation test: [CONFIRMED / FAILED — describe wins count and thread count]
- Strategy: [Threading N=X / Last-Byte Sync / asyncio]

EXPLOITATION:
- Local test: [PASS / FAIL — describe result, e.g. "run 2: 4 wins, balance went negative"]
- Real target: [PASS / FAIL — describe result]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
