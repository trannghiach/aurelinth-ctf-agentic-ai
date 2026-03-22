# Upload Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Validation type: [extension blacklist / MIME check / magic bytes / whitelist+exec / zip slip / none]
- Source file: [FILE:LINE of upload handler]
- Upload directory: [path from source or docker-compose]
- Execution context: [PHP executed by nginx / template render / none]
- Flag location: [path from docker-compose.yml or .env]

CONFIRMATION:
- Isolation test: [CONFIRMED — bypass extension passes check / FAILED]
- Bypass used: [.php5 / MIME spoof / magic bytes prepend / etc.]

EXPLOITATION:
- Payload filename: [shell.php5 or similar]
- Upload response: [status code]
- RCE command tested: [cat /flag or id]
- Local test: [PASS / FAIL — RCE output snippet]
- Real target: [PASS / FAIL]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
