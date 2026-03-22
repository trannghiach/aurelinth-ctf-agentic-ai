# Aurelinth

Multi-agent framework for automating CTF web challenges. Orchestrates a team of specialist AI agents — each focused on a single attack class — through a supervisor loop that routes decisions based on accumulated findings.

Built as a personal portfolio project. Has solved most web challenges at live CTF events. See [results/](results/index.md) for flag screenshots from live runs.

---

## How it works

A target URL is submitted through the monitor UI. The orchestrator runs an initial reconnaissance agent, then hands control to a Gemini-powered supervisor that decides which agent to run next based on what was found. This continues until a flag is extracted or the iteration budget is exhausted.

Two pipelines are supported:

**Blackbox** — no source code. Starts with web recon, then routes to hunters (SQLi, XSS, SSTI, LFI, IDOR, auth bypass, file upload, crypto).

**Whitebox** — source code provided. Runs code reader and dependency checker in parallel, feeds both into a vulnerability reasoner, then routes to auditors matched to the findings.

Each agent runs as an isolated gemini-cli subprocess with a hard timeout. Outputs are stored in MongoDB and summarized into a context string passed to the next agent. All events (agent start/stop, tool calls, flag found) are published to a Redis stream and forwarded live to the browser over SSE.

---

## Architecture

```
Monitor UI (React + Vite)
    |
FastAPI (port 8000)  <->  Redis Stream (SSE bridge)
    |
Orchestrator
    |-- TaskQueue (Redis)
    |-- Context layer (MongoDB)
    +-- Supervisor (Gemini Flash)
            |
        Agent (gemini-cli subprocess, cwd=/tmp/aurelinth)
            +-- Skill (Markdown doc, auto-loaded via ~/.gemini/skills/)
```

---

## Agents

| Pipeline  | Agent                    | Role                               |
|-----------|--------------------------|------------------------------------|
| Blackbox  | web-recon                | Fingerprint, crawl, initial scan   |
| Blackbox  | sqli-hunter              | SQL injection                      |
| Blackbox  | xss-hunter               | Reflected, stored, DOM XSS         |
| Blackbox  | auth-bypasser            | Login bypass, JWT attacks          |
| Blackbox  | lfi-hunter               | LFI, path traversal, RCE via log   |
| Blackbox  | ssti-hunter              | Template injection                 |
| Blackbox  | idor-hunter              | Insecure direct object references  |
| Blackbox  | file-upload-hunter       | Upload bypass, webshell            |
| Blackbox  | crypto-hunter            | Token analysis, weak crypto        |
| Blackbox  | flag-extractor           | Consolidate and confirm flag       |
| Whitebox  | code-reader              | Map routes, sinks, data flows      |
| Whitebox  | dep-checker              | Known CVEs in dependencies         |
| Whitebox  | vuln-reasoner            | Rank vulnerabilities by evidence   |
| Whitebox  | sqli-auditor             | Targeted SQLi with source context  |
| Whitebox  | xss-auditor              | XSS with sink/source tracing       |
| Whitebox  | auth-auditor             | Auth logic flaws                   |
| Whitebox  | lfi-auditor              | Path traversal with code context   |
| Whitebox  | ssti-auditor             | SSTI with template engine known    |
| Whitebox  | upload-auditor           | Upload logic flaws                 |
| Whitebox  | race-condition-auditor   | TOCTOU, concurrent request flaws   |
| Whitebox  | crypto-auditor           | Weak key gen, predictable tokens   |
| Whitebox  | deserialization-auditor  | Unsafe deserialization gadget chains |
| Whitebox  | access-control-auditor   | Privilege escalation paths         |

---

## Stack

- **Orchestrator** — Python, asyncio
- **Agents** — gemini-cli (subprocess), Gemini Flash / Pro routing
- **Skills** — Markdown documents loaded by gemini-cli at runtime
- **Queue** — Redis Streams
- **Storage** — MongoDB (raw outputs), Redis (task state, events)
- **Monitor API** — FastAPI, SSE
- **Monitor UI** — React, Vite
- **Tools used by agents** — httpx, katana, nuclei, ffuf, sqlmap, dalfox, jwt_tool

---

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start infrastructure (Redis, MongoDB)
make infra-up

# Install agent tools (katana, nuclei, dalfox, etc.)
make tools

# Symlink skills into gemini-cli
make skills

# Start monitor
make monitor

# Run a scan from CLI
python run.py --target http://target.ctf --mode blackbox
```

---

## Design decisions

**Subprocess per agent, not API calls.** Each agent runs as a full gemini-cli process with its own tool call loop, retries, and reasoning. A raw API call is a single inference. A subprocess is an autonomous agent. The isolation also means a timeout or crash in one agent does not affect the pipeline.

**Skills are reasoning frameworks, not scripts.** Each SKILL.md tells the agent how to think about a problem — what to look for, how to chain tool calls, how to decide when to stop — without hardcoding any target-specific paths, parameters, or payloads. This makes every skill reusable across different challenges.

**Supervisor drives the loop.** A lightweight Gemini Flash call after each agent decides the next move. This keeps the orchestration logic in AI rather than a rigid decision tree, allowing the pipeline to adapt to what was actually found.

**Anti-hallucination guards in every skill.** Agents are explicitly instructed to report only outputs they observed through tool calls. The output schema enforces structured reporting. Combined with regex extraction on the orchestrator side, this filters narrative noise from findings passed downstream.

---

## Monitor

The monitor UI at `http://localhost:5173` provides a real-time view of agent activity: tool calls, reasoning steps, flags found, and run history. Each event is streamed from Redis to the browser over SSE as it happens.

---

## Status

Active development. Core pipelines are stable. Whitebox pipeline is newer and has seen less live use than blackbox.
