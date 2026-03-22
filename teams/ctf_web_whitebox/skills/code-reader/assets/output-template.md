# Code Reader Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Output structured findings only — no narrative, no raw file dumps.

---

CONTEXT:
- Language: [Python/Flask | PHP | Node | Go | Java]
- Entry point: [filename (single-file or split routes)]
- Templates: [path list or N/A]
- Models: [filename, table count]
- Config: [filename(s) and what secrets they contain]
- Docker: [docker-compose.yml present / absent]

CONFIRMATION:
- Structure mapped: [YES — N files read / NO — inaccessible]
- Flag location: [table.column / env var / hardcoded / unknown]

EXTRACTED:
- Routes: [list of GET/POST /path → handler() — auth state]
- Database: [engine, tables, columns of interest]
- Auth: [mechanism, session type, role field]
- Data flows: [user input → var → sink, one per suspicious path]
- Dependencies: [name==version, one per line — pass to dep_checker]

UNEXPECTED:
- Interesting findings: [hardcoded secrets, plaintext passwords, missing auth, etc.]
- Or N/A

RECOMMENDED NEXT: vuln_reasoner
- Reason: [one sentence summarizing highest-priority finding for vuln_reasoner to trace]
