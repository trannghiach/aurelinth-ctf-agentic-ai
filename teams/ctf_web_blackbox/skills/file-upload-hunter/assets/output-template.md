# File Upload Hunter Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Endpoint: [upload URL]
- Bypass used: [extension bypass / MIME spoof / magic bytes / .htaccess / no validation]

CONFIRMATION:
- Payload filename: [shell.php5 or similar]
- Upload response: [status code and relevant snippet]
- Upload path: [where the file is accessible after upload]

EXPLOITATION:
- Webshell URL: [URL with cmd= parameter]
- RCE command: [e.g. cat /flag.txt]
- Command output: [verbatim from tool output]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
