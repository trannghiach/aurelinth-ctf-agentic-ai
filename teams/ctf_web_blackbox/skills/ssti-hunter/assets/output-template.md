# SSTI Hunter Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Endpoint: [URL + method + param]
- Engine: [Jinja2 / Twig / Smarty / Freemarker / unknown]
- Probe result: [{{7*7}} → 49, or other confirmation]

CONFIRMATION:
- Tool: [manual curl]
- Probe: [exact probe payload used]
- Signal: [output that confirms injection, e.g. "49" in response]

EXPLOITATION:
- Payload: [exact RCE or file-read payload]
- Output: [verbatim output from tool result]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
