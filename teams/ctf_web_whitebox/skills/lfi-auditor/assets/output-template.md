# LFI Auditor Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text outside the markers.

---

CONTEXT:
- Vulnerable pattern: [open(BASE_DIR + user_input) / os.path.join / PHP include / archive traversal]
- Source file: [FILE:LINE]
- Sanitization: [basename / startswith / realpath / none]
- Flag location: [path found in docker-compose.yml or .env]

CONFIRMATION:
- Isolation test: [CONFIRMED — payload resolves to target path / FAILED]
- Bypass used: [direct traversal / absolute path / null byte / none needed]

EXTRACTED:
- File read: [filename]
- Content snippet: [first 100 chars of file content from tool output]

FLAG: [verbatim flag exactly as seen in tool output, or NOT CAPTURED]

UNEXPECTED: [off-scope findings worth supervisor routing, or N/A]
