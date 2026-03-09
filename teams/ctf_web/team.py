# Aurelinth — CTF-Web Team
# Prompt templates for each agent type

from orchestrator.core import AgentType


def build_prompt(agent_type: AgentType, target: str, context: str = "") -> str:
    """Build prompt for each agent, inject context from dependencies."""

    ctx_block = f"\n{context}\n" if context else ""

    templates = {
        AgentType.WEB_RECON: f"""Follow the web-recon skill.

Target: {target}{ctx_block}
Perform full web reconnaissance. Map the complete attack surface.""",

        AgentType.SQLI_HUNTER: f"""Follow the sqli-hunter skill.

Target: {target}{ctx_block}
Hunt for SQL injection vulnerabilities using the recon context above.
Confirm, exploit, and extract data.""",

        AgentType.XSS_HUNTER: f"""Follow the xss-hunter skill.

Target: {target}{ctx_block}
Hunt for XSS vulnerabilities using the recon context above.
Identify context, confirm, and escalate.""",

        AgentType.AUTH_BYPASSER: f"""Follow the auth-bypasser skill.

Target: {target}{ctx_block}
Test all authentication mechanisms using the recon context above.
Attempt bypass and privilege escalation.""",

        AgentType.FLAG_EXTRACTOR: f"""Follow the flag-extractor skill.

Target: {target}{ctx_block}
Flag not yet found. Pursue the highest-probability leads now, then write final report.""",
    }

    return templates[agent_type]