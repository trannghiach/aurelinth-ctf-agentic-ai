# Aurelinth - Context Serialization Layer
# Raw -> Summary + MongoDB pointer -> Clean Context to next agent

import json
from orchestrator.gemini import call, safe_inject

RAW_LIMIT = 3000  # Max chars for raw context, to prevent Gemini overload

def extract_structured(raw: str) -> str:
    """
    Gemini output includes 2 parts: narration + structured findings.
    Take the structured — start from the keyword.
    """
    markers = [
        "TECHNOLOGY:", "ENDPOINTS:", "CONFIRMATION:", "CONTEXT:",
        "BYPASS METHOD:", "SUMMARY:", "EXTRACTED:", "ENUMERATION:"
    ]

    lines = raw.split("\n")
    start_idx = None

    for i, line in enumerate(lines):
        if any(line.strip().startswith(m) for m in markers):
            start_idx = i
            break

    if start_idx is not None:
        return "\n".join(lines[start_idx:]).strip()

    # Can not find marker → fallback 20 last lines
    return "\n".join(lines[-20:]).strip()

def serialize(task_id: str, agent_type: str, raw_output: str, db) -> dict:
    """
    After each agent call, serialize the raw output into a clean context.
    Save raw output in MongoDB for reference, and only pass summary to the next agent.
    """
    
    doc = {
        "task_id": task_id,
        "agent_type": agent_type,
        "raw": raw_output,
    }
    result = db.outputs.insert_one(doc)
    mongo_ref = str(result.inserted_id)
    
    # If the output is short -> use it directly without summarization
    if len(raw_output) <= RAW_LIMIT:
        return {
            "mongo_ref": mongo_ref,
            "summary": extract_structured(raw_output),
            "truncated": False,
        }
        
    # Otherwise, summarize it with Gemini and return the summary + MongoDB reference
    prompt = f"""Summarize the following security tool output into a concise list of key findings.
Keep it under 500 words. Focus on: hosts, endpoints, vulnerabilities, interesting observations.

{safe_inject(raw_output[:8000])}

Return plain text summary only."""

    summary = call("web_recon", prompt, timeout=60)
    
    return {
        "mongo_ref": mongo_ref,
        "summary": summary,
        "truncated": True,
    }
    
    
def build_prompt_context(contexts: list[dict]) -> str:
    """
    Receive list contexts from previous agents -> build into 1 block
    to inject into Gemini prompt for next agent.
    """
    if not contexts:
        return ""
    
    lines = ["## Context from previous agents:"]
    for ctx in contexts:
        lines.append(f"- {ctx.get('agent_type', 'unknown')}: {ctx['summary']}")

    return "\n".join(lines)