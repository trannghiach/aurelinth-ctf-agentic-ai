# Aurelinth Supervisor — Gemini Flash do agent selection based on findings so far
import json
import os
from orchestrator.gemini import call
from orchestrator.core import AgentType, WHITEBOX_AUDITORS

_SKILL_DIR = os.path.join(os.path.dirname(__file__), "..", "teams", "supervisor")

def _load_skill(name: str) -> str:
    path = os.path.join(_SKILL_DIR, f"{name}.md")
    with open(path) as f:
        return f.read()

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

    def _summarize(c: dict) -> str:
        import re
        s = c['summary']
        flag_match = re.search(r"FLAG:.*", s)
        flag_line = f"\n  {flag_match.group(0)}" if flag_match else ""
        return f"- [{c['agent']}]: {s[:800]}{flag_line}"

    summaries = "\n".join(_summarize(c) for c in completed)
    unexpected_block = ""
    if unexpected:
        unexpected_block = "\nUnexpected findings from agents:\n" + "\n".join(
            f"- [{u['agent']}]: {u['finding']}" for u in unexpected
        )

    prompt = f"""{_load_skill("blackbox")}

---

Target: {target}
Flag format: {flag_format or "unknown"}

Completed agents and their findings:
{summaries}
{unexpected_block}

Available agents (not yet run): {", ".join(available) if available else "none"}"""

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

    prompt = f"""{_load_skill("whitebox")}

---

Target: {target}
Flag format: {flag_format or "unknown"}

vuln_reasoner findings (ranked by exploitability):
{vuln_reasoner_summary or "No vuln_reasoner output available"}
{auditor_results_block}

Available auditors (not yet run): {", ".join(available) if available else "none"}"""

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