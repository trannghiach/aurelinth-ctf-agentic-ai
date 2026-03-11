# Aurelinth — CTF-Web Team
from orchestrator.core import AgentType


def load_skill(name: str) -> str:
    import os
    path = os.path.expanduser(f"~/.gemini/skills/{name}/SKILL.md")
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def build_prompt(agent_type: AgentType, target: str,
                 context: str = "", flag_format: str = "") -> str:
    ctx_block  = f"\n{context}\n" if context else ""
    flag_block = f"\nFlag format: {flag_format}\nReport immediately if found.\n" if flag_format else ""

    templates = {
        AgentType.WEB_RECON: f"""Follow the web-recon skill.
Target: {target}{flag_block}{ctx_block}
Perform full web reconnaissance. Map the complete attack surface.""",

        AgentType.SQLI_HUNTER: f"""Follow the sqli-hunter skill.
Target: {target}{flag_block}{ctx_block}
Hunt for SQL injection. Confirm, exploit, extract data.
HARD LIMIT: maximum 10 tool calls.""",

        AgentType.XSS_HUNTER: f"""Follow the xss-hunter skill.
Target: {target}{flag_block}{ctx_block}
Hunt for XSS. Identify context, confirm, escalate.
HARD LIMIT: maximum 6 tool calls.""",

        AgentType.AUTH_BYPASSER: f"""Follow the auth-bypasser skill.
Target: {target}{flag_block}{ctx_block}
Test authentication mechanisms. Attempt bypass and privilege escalation.
HARD LIMIT: maximum 6 tool calls.""",

        AgentType.LFI_HUNTER: f"""Follow the lfi-hunter skill.
Target: {target}{flag_block}{ctx_block}
Hunt for LFI/path traversal. Attempt to read sensitive files, escalate to RCE if possible.
HARD LIMIT: maximum 10 tool calls.""",

        AgentType.SSTI_HUNTER: f"""Follow the ssti-hunter skill.
Target: {target}{flag_block}{ctx_block}
Hunt for SSTI. Identify template engine, confirm, escalate to RCE.
HARD LIMIT: maximum 8 tool calls.""",

        AgentType.IDOR_HUNTER: f"""Follow the idor-hunter skill.
Target: {target}{flag_block}{ctx_block}
Hunt for IDOR and broken access control. Enumerate object references.
HARD LIMIT: maximum 8 tool calls.""",

        AgentType.FILE_UPLOAD_HUNTER: f"""Follow the file-upload-hunter skill.
Target: {target}{flag_block}{ctx_block}
Hunt for file upload vulnerabilities. Bypass filters, attempt webshell upload.
HARD LIMIT: maximum 8 tool calls.""",

        AgentType.FLAG_EXTRACTOR: f"""Follow the flag-extractor skill.
Target: {target}{flag_block}{ctx_block}
Read existing dumps first. Pursue ONE highest-probability lead. Write final report.
HARD LIMIT: maximum 8 tool calls.""",
    }
    return templates[agent_type]