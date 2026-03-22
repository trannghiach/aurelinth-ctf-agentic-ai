# LFI Hunter Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Endpoint: [URL + param]
- Bypass used: [direct traversal / PHP filter wrapper / log poisoning / none]

CONFIRMATION:
- Payload: [exact payload that worked]
- Signal: [what confirmed it, e.g. "root:" in passwd output]

EXTRACTED:
- Files read: [list of files successfully read]
- Content snippet: [first 100 chars of most important file from tool output]

EXPLOITATION:
- RCE method: [log poisoning / PHP wrapper / N/A]
- Command output: [verbatim from tool output, or N/A]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
