"""
Aurelinth sanity checks — run from project root:
  python3 tests/test_sanity.py
"""
import sys
import json
import inspect
import unittest.mock as mock

sys.path.insert(0, "/home/foqs/aurelinth")

from orchestrator.core import scan_flag, scan_flag_section, AgentType
from orchestrator.supervisor import _call_supervisor
from teams.ctf_web_blackbox.team import build_prompt as bb_prompt
from teams.ctf_web_whitebox.team import build_prompt as wb_prompt
import run as r

PASS = "✓"
FAIL = "✗"
errors = []


def check(name, fn):
    try:
        fn()
        print(f"  {PASS}  {name}")
    except Exception as e:
        print(f"  {FAIL}  {name} — {e}")
        errors.append(name)


# ── scan_flag ─────────────────────────────────────────────────────────────────

def test_scan_flag_basic():
    assert scan_flag("the flag is picoCTF{hello_world}", "picoCTF{...}") == "picoCTF{hello_world}"

def test_scan_flag_backtick_false_positive():
    assert scan_flag("looking for `picoCTF{` in /api/{exportId}", "picoCTF{...}") is None

def test_scan_flag_long_content_false_positive():
    long = "picoCTF{" + "y" * 200 + "}"
    assert scan_flag(long, "picoCTF{...}") is None

def test_scan_flag_template_filtered():
    assert scan_flag("format is picoCTF{...}", "picoCTF{...}") is None

def test_scan_flag_section_basic():
    assert scan_flag_section("got FlagY{abc123def456}") == "FlagY{abc123def456}"

def test_scan_flag_section_no_false_positive():
    assert scan_flag_section("endpoint /api/{exportId} is here") is None

# ── run_agent ─────────────────────────────────────────────────────────────────

def test_run_agent_context_override_param():
    assert "context_override" in inspect.signature(r.run_agent).parameters

# ── prompts ───────────────────────────────────────────────────────────────────

def test_blackbox_prompt_tmp():
    p = bb_prompt(AgentType.WEB_RECON, "http://test.com", "", "CTF{...}")
    assert "/tmp/aurelinth/" in p

def test_whitebox_prompt_tmp():
    p = wb_prompt(AgentType.CODE_READER, "http://test.com", "", "CTF{...}", source_code="/tmp/src")
    assert "/tmp/aurelinth/" in p

def test_blackbox_prompt_skill_activation():
    p = bb_prompt(AgentType.SQLI_HUNTER, "http://test.com", "", "CTF{...}")
    assert "activate_skill" in p

def test_whitebox_prompt_skill_activation():
    p = wb_prompt(AgentType.AUTH_AUDITOR, "http://test.com", "", "CTF{...}", source_code="/tmp/src")
    assert "activate_skill" in p

# ── supervisor ────────────────────────────────────────────────────────────────

def test_supervisor_has_retry_and_context():
    fake = json.dumps({
        "next": "sqli_hunter", "retry": None,
        "reason": "sqli confirmed", "context_for_next": "focus on login form",
        "stop": False, "flag": None,
    })
    with mock.patch("orchestrator.supervisor.call", return_value=fake):
        result = _call_supervisor("prompt", ["sqli_hunter"])
    assert "retry" in result
    assert "context_for_next" in result
    assert result["context_for_next"] == "focus on login form"

def test_supervisor_defaults_when_fields_absent():
    fake = json.dumps({"next": "xss_hunter", "reason": "xss found", "stop": False, "flag": None})
    with mock.patch("orchestrator.supervisor.call", return_value=fake):
        result = _call_supervisor("prompt", ["xss_hunter"])
    assert result.get("retry") is None
    assert result.get("context_for_next") is None

def test_supervisor_rejects_unavailable_agent():
    fake = json.dumps({"next": "sqli_hunter", "retry": None, "reason": "x", "stop": False, "flag": None})
    with mock.patch("orchestrator.supervisor.call", return_value=fake):
        result = _call_supervisor("prompt", ["xss_hunter"])  # sqli_hunter not available
    assert result["next"] is None
    assert result["stop"] is True


# ── xss skill files ───────────────────────────────────────────────────────────

from pathlib import Path

XSS_HUNTER  = Path("/home/foqs/aurelinth/teams/ctf_web_blackbox/skills/xss-hunter/SKILL.md").read_text()
XSS_AUDITOR = Path("/home/foqs/aurelinth/teams/ctf_web_whitebox/skills/xss-auditor/SKILL.md").read_text()

def test_xss_hunter_no_double_path():
    assert "/tmp/aurelinth/aurelinth/" not in XSS_HUNTER, "double /tmp/aurelinth/ path still present"

def test_xss_hunter_tool_limit():
    import re
    m = re.search(r"Maximum (\d+) tool calls", XSS_HUNTER)
    assert m and int(m.group(1)) >= 25, f"tool limit too low: {m.group(1) if m else 'not found'}"

def test_xss_hunter_has_interactsh():
    assert "interactsh-client" in XSS_HUNTER, "interactsh-client not in xss-hunter"

def test_xss_hunter_has_dom_xss():
    assert "DOM" in XSS_HUNTER, "no DOM XSS section in xss-hunter"

def test_xss_hunter_has_csp():
    assert "CSP" in XSS_HUNTER, "no CSP section in xss-hunter"

def test_xss_auditor_no_attacker_placeholder():
    assert "http://ATTACKER" not in XSS_AUDITOR, "ATTACKER placeholder still present in xss-auditor"

def test_xss_auditor_tool_limit():
    import re
    m = re.search(r"Maximum (\d+) tool calls", XSS_AUDITOR)
    assert m and int(m.group(1)) >= 25, f"tool limit too low: {m.group(1) if m else 'not found'}"

def test_xss_auditor_has_interactsh():
    assert "interactsh-client" in XSS_AUDITOR, "interactsh-client not in xss-auditor"

def test_xss_auditor_single_shell_call():
    assert "ONE tool call" in XSS_AUDITOR or "one tool call" in XSS_AUDITOR.lower(), \
        "single-subprocess pattern not documented in xss-auditor"


# ── run ───────────────────────────────────────────────────────────────────────

print("\nAurelinth sanity checks")
print("─" * 40)

ALL_CHECKS = [
    ("scan_flag basic match",                   test_scan_flag_basic),
    ("scan_flag backtick false positive",        test_scan_flag_backtick_false_positive),
    ("scan_flag long content false positive",    test_scan_flag_long_content_false_positive),
    ("scan_flag template filtered",              test_scan_flag_template_filtered),
    ("scan_flag_section basic",                  test_scan_flag_section_basic),
    ("scan_flag_section no false positive",      test_scan_flag_section_no_false_positive),
    ("run_agent has context_override param",     test_run_agent_context_override_param),
    ("blackbox prompt has /tmp/aurelinth/",      test_blackbox_prompt_tmp),
    ("whitebox prompt has /tmp/aurelinth/",      test_whitebox_prompt_tmp),
    ("blackbox prompt has activate_skill",       test_blackbox_prompt_skill_activation),
    ("whitebox prompt has activate_skill",       test_whitebox_prompt_skill_activation),
    ("supervisor has retry + context_for_next",  test_supervisor_has_retry_and_context),
    ("supervisor defaults missing fields",       test_supervisor_defaults_when_fields_absent),
    ("supervisor rejects unavailable agent",     test_supervisor_rejects_unavailable_agent),
    # xss
    ("xss-hunter no double /tmp path",           test_xss_hunter_no_double_path),
    ("xss-hunter tool limit >= 25",             test_xss_hunter_tool_limit),
    ("xss-hunter has interactsh",               test_xss_hunter_has_interactsh),
    ("xss-hunter has DOM XSS section",          test_xss_hunter_has_dom_xss),
    ("xss-hunter has CSP section",              test_xss_hunter_has_csp),
    ("xss-auditor no ATTACKER placeholder",     test_xss_auditor_no_attacker_placeholder),
    ("xss-auditor tool limit >= 25",            test_xss_auditor_tool_limit),
    ("xss-auditor has interactsh",              test_xss_auditor_has_interactsh),
    ("xss-auditor single shell call pattern",   test_xss_auditor_single_shell_call),
]

for name, fn in ALL_CHECKS:
    check(name, fn)

print("─" * 40)
if errors:
    print(f"\n{len(errors)} check(s) failed: {', '.join(errors)}")
    sys.exit(1)
else:
    print(f"\nAll {len(ALL_CHECKS)} checks passed.")
