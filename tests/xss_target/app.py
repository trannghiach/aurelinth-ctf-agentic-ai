"""
Minimal XSS test target for Aurelinth xss-hunter validation.
Has:
  - Reflected XSS at /search?q=
  - Stored XSS at /guestbook (POST) + /guestbook (GET display)
  - Admin bot at /report — real Playwright Chromium, full internet access
  - Admin bot at /report-sandboxed — same bot but external HTTP/DNS blocked
    (simulates CTF sandboxed bot — interactsh OOB will get EMPTY, forcing Phase 7 fallback)
  - Profile relay at /profile (GET/POST) — writable bio field, readable without auth
  - Flag at /flag (admin cookie required)

Run:  python3 tests/xss_target/app.py
URL:  http://localhost:7331

Two test scenarios:
  1. POST /report      → OOB works → agent captures flag via interactsh callback
  2. POST /report-sandboxed → OOB blocked → agent must use Phase 7 in-app relay via /profile
"""
import sys
import threading
import time
from flask import Flask, request, redirect, jsonify
from playwright.sync_api import sync_playwright

# Pass --sandbox-only to hide /report and force Phase 7 in-app relay path
SANDBOX_ONLY = "--sandbox-only" in sys.argv

app = Flask(__name__)
FLAG    = "CTF{xss_hunt3r_v4lid4t3d}"
COMMENTS = []
PROFILES = {}   # username → {bio: str}  — in-app relay storage


# ── helpers ──────────────────────────────────────────────────────────────────

def _bot(target: str, block_external: bool) -> None:
    """Run Playwright admin bot. If block_external=True, abort all non-localhost requests."""
    time.sleep(2)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            ctx = browser.new_context()
            ctx.add_cookies([{
                "name":   "session",
                "value":  "ADMIN_SECRET_TOKEN",
                "domain": "localhost",
                "path":   "/",
            }])
            page = ctx.new_page()

            if block_external:
                # Block every request whose host is not localhost / 127.0.0.1
                def _intercept(route, req):
                    host = req.url.split("/")[2].split(":")[0]
                    if host not in ("localhost", "127.0.0.1"):
                        route.abort()
                    else:
                        route.continue_()
                page.route("**/*", _intercept)

            page.goto(target, wait_until="networkidle", timeout=15000)
            time.sleep(5)   # let async XSS payloads finish
            page.close()
            browser.close()
    except Exception as e:
        print(f"[bot{'‑sandboxed' if block_external else ''}] error: {e}")


# ── pages ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    report_line = "" if SANDBOX_ONLY else \
        "  <li>Admin bot (internet access)   → POST /report         url=http://localhost:...</li>\n"
    return f"""
<html><body>
<h1>XSS Test Target</h1>
<ul>
  <li><a href="/search?q=hello">Reflected XSS → /search?q=</a></li>
  <li><a href="/guestbook">Stored XSS → /guestbook</a></li>
{report_line}  <li>Admin bot (sandboxed/no OOB)  → POST /report-sandboxed url=http://localhost:...</li>
  <li>Profile relay (in-app exfil)  → GET/POST /profile?user=attacker</li>
  <li>Flag (admin only)             → GET /flag</li>
</ul>
</body></html>"""


@app.route("/search")
def search():
    q = request.args.get("q", "")
    return f"""
<html><body>
<h2>Search results for: {q}</h2>
<form method=GET action=/search><input name=q value="{q}"><button>Search</button></form>
</body></html>"""


@app.route("/guestbook", methods=["GET", "POST"])
def guestbook():
    if request.method == "POST":
        name = request.form.get("name", "anonymous")
        msg  = request.form.get("message", "")
        COMMENTS.append((name, msg))
        return redirect("/guestbook")

    entries = "".join(f"<div><b>{n}</b>: {m}</div>" for n, m in COMMENTS)
    return f"""
<html><body>
<h2>Guestbook</h2>
{entries}
<hr>
<form method=POST>
  Name: <input name=name><br>
  Message: <textarea name=message></textarea><br>
  <button>Post</button>
</form>
</body></html>"""


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """
    In-app relay endpoint — publicly writable + readable.
    GET  /profile?user=attacker           → returns {"user":"attacker","bio":"..."}
    POST /profile  user=attacker&bio=...  → updates bio, returns {"ok":true}
    XSS payload running in admin context can POST here; attacker reads back via GET.
    """
    if request.method == "POST":
        user = request.form.get("user", "")
        bio  = request.form.get("bio", "")
        if not user:
            return jsonify({"error": "user required"}), 400
        if user not in PROFILES:
            PROFILES[user] = {"bio": ""}
        PROFILES[user]["bio"] = bio
        return jsonify({"ok": True})

    user = request.args.get("user", "")
    if not user:
        return jsonify({"error": "user required"}), 400
    data = PROFILES.get(user, {"bio": ""})
    return jsonify({"user": user, "bio": data["bio"]})


@app.route("/report", methods=["POST"])
def report():
    if SANDBOX_ONLY:
        return "Not found", 404
    url = request.form.get("url", "")
    if not url.startswith("http://localhost"):
        return "invalid url", 400
    threading.Thread(target=_bot, args=(url, False), daemon=True).start()
    return "Report submitted. Admin will review shortly."


@app.route("/report-sandboxed", methods=["POST"])
def report_sandboxed():
    """
    Same as /report but the bot cannot reach external hosts.
    interactsh OOB will get EMPTY — agent must use Phase 7 in-app relay via /profile.
    """
    url = request.form.get("url", "")
    if not url.startswith("http://localhost"):
        return "invalid url", 400
    threading.Thread(target=_bot, args=(url, True), daemon=True).start()
    return "Report submitted. Admin will review shortly (sandboxed)."


@app.route("/flag")
def flag():
    cookie = request.cookies.get("session", "")
    if cookie == "ADMIN_SECRET_TOKEN":
        return FLAG
    return "Forbidden — admin only", 403


if __name__ == "__main__":
    print(f"[*] XSS target running at http://localhost:7331")
    print(f"[*] Flag: {FLAG}")
    if SANDBOX_ONLY:
        print(f"[*] Mode: SANDBOX-ONLY — /report disabled, only /report-sandboxed available")
        print(f"[*] External HTTP blocked in bot — OOB will get EMPTY, Phase 7 relay required")
    else:
        print(f"[*] POST /report           → bot with full internet (OOB works)")
        print(f"[*] POST /report-sandboxed → bot with external HTTP blocked (Phase 7 required)")
    app.run(host="0.0.0.0", port=7331, debug=False)
