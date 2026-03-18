# Aurelinth — Pre-run health check
# Verifies infra, gemini-cli, skill symlinks, and key tools before wasting a run.

import os
import shutil
import subprocess
from pathlib import Path

SKILLS_DIR   = Path.home() / ".gemini" / "skills"
GEMINI_BIN   = "/usr/local/bin/gemini"

REQUIRED_SKILLS = [
    # blackbox
    "web-recon", "sqli-hunter", "xss-hunter", "auth-bypasser",
    "lfi-hunter", "ssti-hunter", "idor-hunter", "file-upload-hunter",
    "crypto-hunter", "flag-extractor",
    # whitebox
    "code-reader", "dep-checker", "vuln-reasoner",
    "sqli-auditor", "xss-auditor", "auth-auditor", "lfi-auditor",
    "ssti-auditor", "access-control-auditor", "upload-auditor",
    "race-condition-auditor", "crypto-auditor", "deserialization-auditor",
]

REQUIRED_TOOLS = [
    ("httpx",    ["/home/foqs/.pdtm/go/bin/httpx"]),
    ("katana",   ["/home/foqs/.pdtm/go/bin/katana", "/home/foqs/go/bin/katana"]),
    ("nuclei",   ["/home/foqs/.pdtm/go/bin/nuclei", "/home/foqs/go/bin/nuclei"]),
    ("ffuf",     ["/usr/bin/ffuf"]),
    ("dalfox",   ["/home/foqs/go/bin/dalfox"]),
    ("sqlmap",   ["/home/foqs/tools/sqlmap/sqlmap.py"]),
    ("jwt_tool", ["/home/foqs/tools/jwt_tool/jwt_tool.py"]),
    ("curl",     None),   # system tool — just check PATH
    ("openssl",  None),
    ("java",     None),
]


def _ok(msg):    return {"status": "ok",    "msg": msg}
def _warn(msg):  return {"status": "warn",  "msg": msg}
def _error(msg): return {"status": "error", "msg": msg}


def check_infra() -> list[dict]:
    results = []

    # Redis
    try:
        from memory import get_redis
        r = get_redis()
        r.ping()
        results.append(_ok("Redis reachable"))
    except Exception as e:
        results.append(_error(f"Redis unreachable: {e}"))

    # MongoDB
    try:
        from memory import get_mongo
        db = get_mongo()
        db.command("ping")
        results.append(_ok("MongoDB reachable"))
    except Exception as e:
        results.append(_error(f"MongoDB unreachable: {e}"))

    return results


def check_gemini() -> list[dict]:
    results = []
    if not os.path.isfile(GEMINI_BIN):
        # fallback: check PATH
        if not shutil.which("gemini"):
            return [_error(f"gemini-cli not found at {GEMINI_BIN} or in PATH")]
        bin_path = shutil.which("gemini")
    else:
        bin_path = GEMINI_BIN

    try:
        out = subprocess.run(
            [bin_path, "--version"],
            capture_output=True, text=True, timeout=5
        )
        version = (out.stdout or out.stderr).strip().splitlines()[0]
        results.append(_ok(f"gemini-cli found: {version}"))
    except subprocess.TimeoutExpired:
        results.append(_warn("gemini-cli found but --version timed out"))
    except Exception as e:
        results.append(_warn(f"gemini-cli found but version check failed: {e}"))

    return results


def check_symlinks() -> list[dict]:
    results = []
    if not SKILLS_DIR.exists():
        return [_error(f"skills dir missing: {SKILLS_DIR}")]

    linked = {p.name: p for p in SKILLS_DIR.iterdir() if p.is_symlink()}

    for skill in REQUIRED_SKILLS:
        if skill not in linked:
            results.append(_error(f"symlink missing: {skill}"))
        elif not linked[skill].exists():
            target = os.readlink(linked[skill])
            results.append(_error(f"symlink broken: {skill} → {target}"))
        else:
            results.append(_ok(f"skill ok: {skill}"))

    return results


def check_tools() -> list[dict]:
    results = []
    for name, paths in REQUIRED_TOOLS:
        if paths is None:
            # system tool
            if shutil.which(name):
                results.append(_ok(f"tool ok: {name}"))
            else:
                results.append(_warn(f"tool missing: {name}"))
        else:
            found = next((p for p in paths if os.path.isfile(p)), None)
            if found:
                results.append(_ok(f"tool ok: {name} ({found})"))
            else:
                results.append(_warn(f"tool missing: {name} (checked: {', '.join(paths)})"))

    return results


def run_health_check(verbose: bool = False) -> bool:
    """
    Run all checks. Print results. Return True if no errors (warnings are ok).
    """
    sections = [
        ("Infrastructure",  check_infra()),
        ("gemini-cli",      check_gemini()),
        ("Skill symlinks",  check_symlinks()),
        ("Tools",           check_tools()),
    ]

    has_error = False
    print("\n── Aurelinth health check ──────────────────────")
    for section, results in sections:
        errors  = [r for r in results if r["status"] == "error"]
        warns   = [r for r in results if r["status"] == "warn"]
        oks     = [r for r in results if r["status"] == "ok"]

        if errors:
            icon = "✗"
            has_error = True
        elif warns:
            icon = "⚠"
        else:
            icon = "✓"

        summary = f"{len(oks)} ok"
        if warns:   summary += f", {len(warns)} warn"
        if errors:  summary += f", {len(errors)} error"
        print(f"  {icon}  {section}: {summary}")

        if verbose or errors or warns:
            for r in results:
                if r["status"] == "ok" and not verbose:
                    continue
                sym = {"ok": "  ✓", "warn": "  ⚠", "error": "  ✗"}[r["status"]]
                print(f"       {sym}  {r['msg']}")

    print("────────────────────────────────────────────────")
    if has_error:
        print("  BLOCKED — fix errors before running\n")
    else:
        print("  Ready.\n")

    return not has_error


def health_summary() -> dict:
    """Return structured summary for API endpoint."""
    sections = {
        "infra":    check_infra(),
        "gemini":   check_gemini(),
        "symlinks": check_symlinks(),
        "tools":    check_tools(),
    }
    overall = "ok"
    for results in sections.values():
        for r in results:
            if r["status"] == "error":
                overall = "error"
                break
            if r["status"] == "warn" and overall != "error":
                overall = "warn"
    return {"overall": overall, "checks": sections}


if __name__ == "__main__":
    import sys
    ok = run_health_check(verbose=True)
    sys.exit(0 if ok else 1)
