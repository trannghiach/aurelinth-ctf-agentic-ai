# Vuln Reasoner Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
One CONFIRMATION block per finding. Rank HIGH before MEDIUM before LOW.

---

CONTEXT:
- Source: [code_reader + dep_checker findings summary]
- Candidates triaged: [count]
- Verified with source reads: [count]

CONFIRMATION:
Finding #[N]
- Suspected: [sqli / idor / xss / ssti / lfi / auth bypass / race / deserial / crypto]
- Confidence: [HIGH / MEDIUM / LOW]
- Agent: [auditor agent name]
- File: [FILE:LINE]
- Entry point: [route + parameter]
- Source: [where user input enters]
- Flow: [variable path to sink]
- Sink: [dangerous function / query]
- Sanitization: [description or "none"]
- Exploitable: [YES / MAYBE / NO — reason]
- Flag path: [exact exploit chain to flag]

[repeat CONFIRMATION block for each finding]

UNEXPECTED:
- Findings that don't fit standard categories, or N/A

RECOMMENDED NEXT: [single agent name for highest-priority finding]
- Reason: [confidence + flag path summary, one sentence]
