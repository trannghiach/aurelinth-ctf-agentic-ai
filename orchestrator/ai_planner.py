# Aurelinth - AI Planner
# Gemini 3.1 Pro do strategy - Python execute

from orchestrator.core import Task, AgentType, make_id, default_ctf_pipeline
from orchestrator.gemini import call_json
import uuid

VALID_AGENTS = {agent.value for agent in AgentType}

def plan_campaign(target: str, notes: str = "") -> list[Task]:
    """
    Gemini 3.1 Pro plan the campaign
    If AI fail or return invalid plan -> fallback to default pipeline
    """
    prompt = f"""You are a senior CTF web security expert planning an attack campaign.

Target: {target}
Notes: {notes if notes else "Standard CTF web challenge"}
Available agents: {", ".join(VALID_AGENTS)}

Return ONLY a JSON array. No explanation, no markdown. Example:
[
  {{"id": "a1b2c3d4", "agent_type": "web_recon", "depends_on": []}},
  {{"id": "e5f6a7b8", "agent_type": "sqli_hunter", "depends_on": ["a1b2c3d4"]}}
]

Rules:
- web_recon must always be first with empty depends_on
- flag_extractor must always be last
- sqli_hunter, xss_hunter, auth_bypasser depend on web_recon
- use 8-char hex ids"""

    try:
        raw = call_json("plan_campaign", prompt, timeout=60)
        tasks = _parse_plan(raw, target)
        if not tasks:
            raise ValueError("Empty plan returned")
        return tasks
    except Exception as e:
        print(f"[planner] AI plan failed ({e}) -> using default pipeline")
        return default_ctf_pipeline(target)

def _parse_plan(raw: list, target: str) -> list[Task]:
    """
    Validate AI output -> list[Task].
    Return [] if invalid.
    """
    if not isinstance(raw, list):
        return []
    
    tasks = []
    seen_ids = set()

    for item in raw:
        agent_type = item.get("agent_type", "")
        task_id = item.get("id", make_id())
        depends_on = item.get("depends_on", [])
        
        if agent_type not in VALID_AGENTS:
            print(f"[planner] Unknown agent '{agent_type}', skipping")
            continue    
        
        # Only keep dependencies that are defined in the plan
        valid_deps = [dep for dep in depends_on if dep in seen_ids]
        
        tasks.append(Task(
            id = task_id,
            agent_type = AgentType(agent_type),
            target = target,
            depends_on = valid_deps
        ))
        seen_ids.add(task_id)
        
    return tasks

def should_pivot(target: str, findings_summary: str) -> dict:
    """
    Ask Gemini 3.1 Pro wether we should pivot to another target based on current findings.
    Python decide wether excute pivot or not. AI only suggest.
    """
    prompt = f"""You are analyzing partial CTF findings to decide if the attack strategy should change.

Target: {target}
Findings so far: {findings_summary}

Return ONLY JSON:
{{
  "pivot": true or false,
  "reason": "one sentence",
  "focus": "what to prioritize if pivot is true"
}}"""

    try:
        return call_json("should_pivot", prompt, timeout=60)
    except Exception:
        return {"pivot": False, "reason": "AI analysis failed", "focus": ""}


