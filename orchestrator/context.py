# Aurelinth - Context Serialization Layer
# Raw -> Structured findings + MongoDB pointer -> Clean context for next agent

SUMMARY_CAP = 20_000  # hard char cap — well within Gemini's 1M token window

def extract_structured(raw: str) -> str:
    """
    Strip agent narration and tool-call noise.
    Start from the first structured findings marker; fallback to last 30 lines.
    """
    markers = [
        "TECHNOLOGY:", "ENDPOINTS:", "CONFIRMATION:", "CONTEXT:",
        "BYPASS METHOD:", "SUMMARY:", "EXTRACTED:", "ENUMERATION:"
    ]
    lines = raw.split("\n")
    for i, line in enumerate(lines):
        if any(line.strip().startswith(m) for m in markers):
            return "\n".join(lines[i:]).strip()[:SUMMARY_CAP]
    return "\n".join(lines[-30:]).strip()[:SUMMARY_CAP]


def serialize(task_id: str, agent_type: str, raw_output: str, db) -> dict:
    """
    Persist raw output to MongoDB; return structured findings as summary.
    No Gemini summarization — extract_structured() is sufficient and avoids
    an extra API call, extra latency, and risk of losing FLAG: lines.
    """
    if not raw_output or not raw_output.strip():
        return {"mongo_ref": None, "summary": "[No output]"}

    mongo_ref = str(db.outputs.insert_one({
        "task_id":    task_id,
        "agent_type": agent_type,
        "raw":        raw_output,
    }).inserted_id)

    return {
        "mongo_ref": mongo_ref,
        "summary":   extract_structured(raw_output),
    }


def build_prompt_context(contexts: list[dict]) -> str:
    """Build a single context block to inject into the next agent's prompt."""
    if not contexts:
        return ""
    lines = ["## Context from previous agents:"]
    for ctx in contexts:
        lines.append(f"- {ctx.get('agent_type', 'unknown')}: {ctx['summary']}")
    return "\n".join(lines)
