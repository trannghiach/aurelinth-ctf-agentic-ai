# Aurelinth — CTF-Web Blackbox Team
# Skills are auto-loaded by gemini-cli from ~/.gemini/skills/ symlinks.
# This file only builds the prompt — it does NOT inject skill content.

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


def build_prompt(
    agent_type: AgentType,
    target: str,
    context: str = "",
    flag_format: str = "",
) -> str:
    """
    Build the prompt for a blackbox agent.
    Skills are auto-loaded by gemini-cli — prompts only need to reference skill name
    and provide target + context.
    """
    fb  = _flag_block(flag_format)
    ctx = _ctx_block(context)

    templates = {
        AgentType.WEB_RECON: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='web-recon'. Do not make any other tool call before activating the skill.\n"
            f"You are web-recon. Do NOT activate any other skill.\n"
            f"Follow the web-recon skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Perform reconnaissance ONLY. Map attack surface, then stop."
            f"HARD LIMIT: maximum 50 tool calls."
        ),
        AgentType.SQLI_HUNTER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='sqli-hunter'. Do not make any other tool call before activating the skill.\n"
            f"You are sqli-hunter. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Hunt for SQL injection. Confirm, exploit, extract data.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.XSS_HUNTER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='xss-hunter'. Do not make any other tool call before activating the skill.\n"
            f"You are xss-hunter. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Hunt for XSS. Identify context, confirm, escalate.\n"
            f"HARD LIMIT: maximum 15 tool calls."
        ),
        AgentType.AUTH_BYPASSER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='auth-bypasser'. Do not make any other tool call before activating the skill.\n"
            f"You are auth-bypasser. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Test authentication mechanisms. Attempt bypass and privilege escalation.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.LFI_HUNTER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='lfi-hunter'. Do not make any other tool call before activating the skill.\n"
            f"You are lfi-hunter. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Hunt for LFI/path traversal. Read sensitive files, escalate to RCE if possible.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.SSTI_HUNTER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='ssti-hunter'. Do not make any other tool call before activating the skill.\n"
            f"You are ssti-hunter. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Hunt for SSTI. Identify template engine, confirm, escalate to RCE.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.IDOR_HUNTER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='idor-hunter'. Do not make any other tool call before activating the skill.\n"
            f"You are idor-hunter. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Hunt for IDOR and broken access control. Enumerate object references.\n"
            f"HARD LIMIT: maximum 15 tool calls."
        ),
        AgentType.FILE_UPLOAD_HUNTER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='file-upload-hunter'. Do not make any other tool call before activating the skill.\n"
            f"You are file-upload-hunter. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Hunt for file upload vulnerabilities. Bypass filters, attempt webshell upload.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.CRYPTO_HUNTER: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='crypto-hunter'. Do not make any other tool call before activating the skill.\n"
            f"You are crypto-hunter. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Analyze cryptographic tokens found in web_recon context.\n"
            f"Identify token type, decode header, pick attack path, forge admin token.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
        AgentType.FLAG_EXTRACTOR: (
            f"YOUR VERY FIRST TOOL CALL MUST BE activate_skill with name='flag-extractor'. Do not make any other tool call before activating the skill.\n"
            f"You are flag-extractor. Do NOT activate any other skill.\n"
            f"Target: {target}{fb}{ctx}"
            f"Read existing dumps first. Pursue ONE highest-probability lead. Write final report.\n"
            f"HARD LIMIT: maximum 20 tool calls."
        ),
    }

    prompt = templates.get(agent_type)
    if prompt is None:
        raise ValueError(
            f"[ctf_web_blackbox/team.py] No prompt template for agent: {agent_type}"
        )
    return prompt + _TMP