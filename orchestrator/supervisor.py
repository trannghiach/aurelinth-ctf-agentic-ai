# Aurelinth Supervisor — Gemini Flash do agent selection based on findings so far
import json
from orchestrator.gemini import call
from orchestrator.core import AgentType, WHITEBOX_AUDITORS

# Blackbox: exclude infrastructure agents that are handled by run.py directly
BLACKBOX_AGENTS = [
    a.value for a in AgentType
    if a not in {
        AgentType.WEB_RECON,
        AgentType.FLAG_EXTRACTOR,
        # exclude all whitebox agents from blackbox pool
        AgentType.CODE_READER,
        AgentType.DEP_CHECKER,
        AgentType.VULN_REASONER,
        *WHITEBOX_AUDITORS,
    }
]

# Whitebox: supervisor only picks auditors — infrastructure runs before supervisor loop
WHITEBOX_AGENT_VALUES = [a.value for a in WHITEBOX_AUDITORS]


def decide(
    target: str,
    flag_format: str,
    completed: list[dict],   # [{"agent": "web_recon", "summary": "..."}]
    unexpected: list[dict],  # [{"agent": "sqli_hunter", "finding": "..."}]
    already_ran: set[str],
    mode: str = "blackbox",  # "blackbox" | "whitebox"
) -> dict:
    """
    Ask Gemini Flash to decide next agent based on findings so far.
    Returns:
      {
        "next": "agent_name_or_null",
        "reason": "one sentence — cite specific evidence",
        "stop": false,
        "flag": null
      }
    """
    if mode == "whitebox":
        return _decide_whitebox(target, flag_format, completed, already_ran)
    else:
        return _decide_blackbox(target, flag_format, completed, unexpected, already_ran)


def _decide_blackbox(
    target: str,
    flag_format: str,
    completed: list[dict],
    unexpected: list[dict],
    already_ran: set[str],
) -> dict:
    available = [a for a in BLACKBOX_AGENTS if a not in already_ran]

    summaries = "\n".join(
        f"- [{c['agent']}]: {c['summary'][:800]}" for c in completed
    )
    unexpected_block = ""
    if unexpected:
        unexpected_block = "\nUnexpected findings from agents:\n" + "\n".join(
            f"- [{u['agent']}]: {u['finding']}" for u in unexpected
        )

    prompt = f"""You are a CTF web security supervisor. Based on findings so far,
decide which single agent to run next.

Target: {target}
Flag format: {flag_format or "unknown"}

Completed agents and their findings:
{summaries}
{unexpected_block}

Available agents (not yet run): {", ".join(available) if available else "none"}

Rules:
- You have NO tools. Do not attempt to use any tools or read any files.
- Pick the ONE most promising agent based on actual evidence in findings
- If findings strongly suggest a specific vulnerability → pick matching agent
- If no clear evidence for remaining agents → set next=null, stop=true
- If all high-value agents already ran and no flag found → stop=true
- If findings contain a flag matching {flag_format or "CTF flag format"} → stop=true, flag=<value>
- Do not run agents just because they haven't run yet — only run if evidence supports it
- If the last completed agent produced weak/incomplete output (missing endpoints, no findings, too short) → set retry=<agent_name> instead of next, and explain what was missing
- Each agent can only be retried ONCE — do not retry an agent marked as already_retried

Return ONLY JSON, no markdown:
{{
  "next": "agent_name_or_null",
  "retry": null,
  "reason": "one sentence why — cite specific evidence from findings",
  "context_for_next": "focused 2-3 sentence briefing for the next agent — only what is directly relevant to its task, nothing else",
  "stop": false,
  "flag": null
}}"""

    return _call_supervisor(prompt, available)


def _decide_whitebox(
    target: str,
    flag_format: str,
    completed: list[dict],
    already_ran: set[str],
) -> dict:
    available = [a for a in WHITEBOX_AGENT_VALUES if a not in already_ran]

    # Extract vuln_reasoner findings separately — they are the primary signal
    vuln_reasoner_summary = ""
    other_summaries = []
    for c in completed:
        if c["agent"] == "vuln_reasoner":
            vuln_reasoner_summary = c["summary"]
        elif c["agent"] not in {"code_reader", "dep_checker"}:
            # Include completed auditor results
            other_summaries.append(f"- [{c['agent']}]: {c['summary'][:300]}")

    auditor_results_block = ""
    if other_summaries:
        auditor_results_block = "\nCompleted auditors:\n" + "\n".join(other_summaries)

    prompt = f"""You are a CTF web security supervisor for a WHITEBOX challenge.
vuln_reasoner has already analyzed the source code and produced ranked findings.
Your job: pick the ONE auditor that targets the highest-confidence finding not yet attempted.

Target: {target}
Flag format: {flag_format or "unknown"}

vuln_reasoner findings (ranked by exploitability):
{vuln_reasoner_summary or "No vuln_reasoner output available"}
{auditor_results_block}

Available auditors (not yet run): {", ".join(available) if available else "none"}

Auditor → vulnerability mapping:
- sqli_auditor            → SQL injection
- xss_auditor             → Cross-site scripting
- auth_auditor            → Auth bypass, JWT forge, session manipulation
- lfi_auditor             → LFI, path traversal
- ssti_auditor            → Server-side template injection
- access_control_auditor  → IDOR, missing ownership check
- upload_auditor          → File upload bypass
- race_condition_auditor  → TOCTOU, concurrent state
- crypto_auditor          → Weak crypto, predictable token, ECB, padding oracle
- deserialization_auditor → pickle, yaml.load, PHP unserialize

Rules:
- You have NO tools. Do not attempt to use any tools or read any files.
- ALWAYS follow vuln_reasoner ATTACK RECOMMENDATION if present — it ranked findings for you
- Pick auditor matching the HIGHEST confidence finding not yet run
- If a completed auditor FAILED → pick the next highest confidence finding
- If vuln_reasoner output is missing or unclear → stop=true
- If all HIGH/MEDIUM findings have been attempted → stop=true
- If findings contain a flag matching {flag_format or "CTF flag format"} → stop=true, flag=<value>
- Do NOT pick an auditor without a corresponding FINDING in vuln_reasoner output
- If a completed auditor produced no exploitation attempt or vague output → set retry=<auditor_name> instead of next
- Each auditor can only be retried ONCE — do not retry an auditor marked as already_retried

Return ONLY JSON, no markdown:
{{
  "next": "auditor_name_or_null",
  "retry": null,
  "reason": "one sentence — cite specific FINDING from vuln_reasoner (file, line, confidence)",
  "context_for_next": "focused 2-3 sentence briefing: the exact vulnerability, file, line, and what to target — strip everything unrelated",
  "stop": false,
  "flag": null
}}"""

    return _call_supervisor(prompt, available)


def _call_supervisor(prompt: str, available: list[str]) -> dict:
    try:
        raw = call("supervisor", prompt, timeout=60)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        result = json.loads(clean)

        # Validate next agent is actually available
        if result.get("next") and result["next"] not in available:
            print(f"[supervisor] picked unavailable agent '{result['next']}' → stopping")
            result["next"] = None
            result["stop"] = True

        # Ensure expected keys exist with defaults
        result.setdefault("retry", None)
        result.setdefault("context_for_next", None)

        return result

    except Exception as e:
        print(f"[supervisor] decision failed ({e}) → stopping")
        return {"next": None, "reason": f"supervisor error: {e}", "stop": True, "flag": None}