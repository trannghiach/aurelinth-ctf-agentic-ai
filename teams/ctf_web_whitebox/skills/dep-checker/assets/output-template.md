# Dep Checker Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Output structured findings only — no narrative.

---

CONTEXT:
- Dependency file: [path read, e.g. SOURCE_CODE/requirements.txt]
- Libraries scanned: [count]

CONFIRMATION:
- OSV queries completed: [count / count attempted]
- Hardcoded secrets found: [YES — describe / NO]

EXTRACTED:
- Vulnerable libraries: [CVE-ID — name==version — severity — description (one per line)]
- Non-vulnerable libraries: [name==version — no CVE (one per line)]
- Exploitability assessments: [CVE-ID — YES/NO/LOW — evidence from grep]

UNEXPECTED:
- Other security-relevant findings: [debug mode, unsafe config, etc.]
- Or N/A

RECOMMENDED NEXT: [agent name, e.g. auth_auditor or vuln_reasoner]
- Reason: [priority 1 CVE or finding, one sentence]
