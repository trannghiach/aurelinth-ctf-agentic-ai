# Aurelinth Supervisor — Gemini Flash do agent selection based on findings so far
import json
from orchestrator.gemini import call
from orchestrator.core import AgentType

AVAILABLE_AGENTS = [
    a.value for a in AgentType
    if a not in {AgentType.WEB_RECON, AgentType.FLAG_EXTRACTOR}
]


def decide(
    target: str,
    flag_format: str,
    completed: list[dict],   # [{"agent": "web_recon", "summary": "..."}]
    unexpected: list[dict],  # [{"agent": "sqli_hunter", "finding": "..."}]
    already_ran: set[str],
) -> dict:
    """
    Ask Gemini Flash to decide next agent based on findings so far.
    Returns:
      {
        "next": "lfi_hunter",   # or null
        "reason": "...",
        "stop": false,
        "flag": null
      }
    """
    available = [a for a in AVAILABLE_AGENTS if a not in already_ran]

    summaries = "\n".join(
        f"- [{c['agent']}]: {c['summary'][:400]}" for c in completed
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
- Pick the ONE most promising agent based on actual evidence in findings
- If findings contain a flag matching {flag_format or "CTF flag format"} -> set stop=true, flag=<value>
- If no more promising agents -> set next=null, stop=true
- Do not repeat agents already run
- Prioritize unexpected findings

Return ONLY JSON, no markdown:
{{
  "next": "agent_name_or_null",
  "reason": "one sentence why",
  "stop": false,
  "flag": null
}}"""

    try:
        raw = call("supervisor", prompt, timeout=60)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        result = json.loads(clean)

        # Validate next agent
        if result.get("next") and result["next"] not in available:
            result["next"] = None
            result["stop"] = True

        return result

    except Exception as e:
        print(f"[supervisor] decision failed ({e}) -> stopping")
        return {"next": None, "reason": f"supervisor error: {e}", "stop": True, "flag": None}