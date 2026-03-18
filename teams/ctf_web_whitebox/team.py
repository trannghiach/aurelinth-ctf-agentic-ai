# Aurelinth — CTF-Web Whitebox Team
# Skills are auto-loaded by gemini-cli from ~/.gemini/skills/ symlinks.
# This file only builds the prompt — it does NOT inject skill content.
#
# Extra args vs blackbox:
#   local_target — spun-up local instance (mày đã docker up sẵn)
#   source_code  — path to challenge source on disk

from orchestrator.core import AgentType


def _flag_block(flag_format: str) -> str:
    if not flag_format:
        return ""
    return f"\nFlag format: {flag_format}\nReport the flag immediately if found.\n"


def _ctx_block(context: str) -> str:
    if not context:
        return ""
    return f"\n{context}\n"


_TMP = "\nIMPORTANT: All temporary files (scripts, payloads, outputs, keys) MUST be written to /tmp/aurelinth/ — never write directly to /tmp/.\n"


def _target_block(target: str, local_target: str, source_code: str) -> str:
    lines = [f"Real target : {target}"]
    if local_target:
        lines.append(f"Local target: {local_target}  ← test exploits here first")
    if source_code:
        lines.append(f"Source code : {source_code}")
    return "\n".join(lines)


def build_prompt(
    agent_type: AgentType,
    target: str,
    context: str = "",
    flag_format: str = "",
    local_target: str = "",
    source_code: str = "",
) -> str:
    """
    Build the prompt for a whitebox agent.
    Skills are auto-loaded by gemini-cli — prompts only need to reference skill name
    and provide target + source_code path + context.
    """
    fb    = _flag_block(flag_format)
    ctx   = _ctx_block(context)
    tgt   = _target_block(target, local_target, source_code)

    templates = {

        # ── Infrastructure ────────────────────────────────────────────

        AgentType.CODE_READER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='code-reader'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are code-reader. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"Map the full source structure. Identify entry points, data flows, "
            f"auth mechanisms, and database interactions.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.DEP_CHECKER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='dep-checker'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are dep-checker. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"Parse all dependency files. Flag any known-vulnerable versions with CVE IDs.\n"
            f"HARD LIMIT: maximum 10 tool calls."
        ),
        AgentType.VULN_REASONER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='vuln-reasoner'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are vuln-reasoner. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"Reason about every suspected vulnerability. For each finding output:\n"
            f"  SUSPECTED, FILE, LINE, ENTRY POINT, SINK, DATA FLOW, SANITIZATION, CONFIDENCE.\n"
            f"Rank findings by exploitability. Do NOT attempt exploitation.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),

        # ── Auditors ──────────────────────────────────────────────────

        AgentType.SQLI_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='sqli-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are sqli-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the vulnerable code location from vuln_reasoner findings.\n"
            f"1. Write and run an isolation test to confirm the logic flaw.\n"
            f"2. Craft a targeted exploit script.\n"
            f"3. Test against local target.\n"
            f"4. Attack real target and extract the flag.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.XSS_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='xss-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are xss-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the vulnerable code location from vuln_reasoner findings.\n"
            f"1. Confirm output encoding flaw via isolation test.\n"
            f"2. Craft payload matching the exact rendering context.\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 15 tool calls."
        ),
        AgentType.AUTH_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='auth-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are auth-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the auth flow from vuln_reasoner findings.\n"
            f"1. Write isolation test confirming the bypass logic.\n"
            f"2. Craft exploit (JWT forge / session manipulation / logic skip).\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.LFI_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='lfi-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are lfi-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the vulnerable file read path from vuln_reasoner findings.\n"
            f"1. Confirm path traversal logic via isolation test.\n"
            f"2. Craft payload to read target file.\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.SSTI_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='ssti-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are ssti-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the vulnerable render call from vuln_reasoner findings.\n"
            f"1. Confirm template injection via isolation test (match engine from imports).\n"
            f"2. Craft payload for RCE or direct flag read.\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.ACCESS_CONTROL_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='access-control-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are access-control-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the missing ownership check from vuln_reasoner findings.\n"
            f"1. Confirm IDOR/missing check via isolation test.\n"
            f"2. Identify the exact object ID or parameter to manipulate.\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 15 tool calls."
        ),
        AgentType.UPLOAD_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='upload-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are upload-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the upload validation logic from vuln_reasoner findings.\n"
            f"1. Confirm bypass via isolation test (extension check, MIME, magic bytes).\n"
            f"2. Craft malicious file and upload request.\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.RACE_CONDITION_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='race-condition-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are race-condition-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the TOCTOU window from vuln_reasoner findings.\n"
            f"1. Identify the exact race window in code (check-then-act gap).\n"
            f"2. Write concurrent exploit script.\n"
            f"3. Test against local target with timing tuning.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.CRYPTO_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='crypto-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are crypto-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the crypto weakness from vuln_reasoner findings.\n"
            f"1. Confirm weakness via isolation test (predictable seed / weak algo / reuse).\n"
            f"2. Write decryption or forgery script.\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.DESERIALIZATION_AUDITOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='deserialization-auditor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are deserialization-auditor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"You already know the unsafe deserialization sink from vuln_reasoner findings.\n"
            f"1. Confirm exploitable gadget chain via isolation test.\n"
            f"2. Craft malicious payload (pickle / yaml / json with __reduce__).\n"
            f"3. Test against local target.\n"
            f"4. Attack real target.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),

        # ── Shared ────────────────────────────────────────────────────

        AgentType.FLAG_EXTRACTOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='flag-extractor'. "
            f"Do not read any file, list any directory, or run any command before activating the skill.\n"
            f"You are flag-extractor. Do NOT activate any other skill.\n"
            f"{tgt}{fb}{ctx}"
            f"Review all agent findings. Pursue ONE highest-probability lead.\n"
            f"Write final report with exploit path and flag.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
    }

    prompt = templates.get(agent_type)
    if prompt is None:
        raise ValueError(
            f"[ctf_web_whitebox/team.py] No prompt template for agent: {agent_type}"
        )
    return prompt + _TMP