"""
Minimal XSS test target for Aurelinth xss-hunter validation.
Has:
  - Reflected XSS at /search?q=
  - Stored XSS at /guestbook (POST) + /guestbook (GET display)
  - Admin bot at /report — uses Playwright headless Chromium (real JS execution)
  - Flag hidden in admin-only /flag (requires admin cookie)

Run:  python3 tests/xss_target/app.py
URL:  http://localhost:7331

Admin bot executes JavaScript — XSS payloads (fetch, Image beacon, etc.) actually fire.
interactsh OOB will receive callbacks when payloads run in the bot's browser context.
"""
import threading
import time
from flask import Flask, request, redirect
from playwright.sync_api import sync_playwright

app = Flask(__name__)
FLAG = "CTF{xss_hunt3r_v4lid4t3d}"
COMMENTS = []

@app.route("/")
def index():
    return """
<html><body>
<h1>XSS Test Target</h1>
<ul>
  <li><a href="/search?q=hello">Reflected XSS → /search?q=</a></li>
  <li><a href="/guestbook">Stored XSS → /guestbook</a></li>
  <li>Admin bot → POST /report with url=...</li>
  <li>Flag endpoint (admin only) → /flag</li>
</ul>
</body></html>"""

@app.route("/search")
def search():
    q = request.args.get("q", "")
    # VULNERABLE: raw reflection, no escaping
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
        COMMENTS.append((name, msg))  # stored unescaped
        return redirect("/guestbook")

    entries = "".join(
        f"<div><b>{n}</b>: {m}</div>" for n, m in COMMENTS
    )
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

@app.route("/report", methods=["POST"])
def report():
    url = request.form.get("url", "")
    if not url.startswith("http://localhost"):
        return "invalid url", 400

    def bot_visit(target):
        time.sleep(2)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                ctx = browser.new_context()
                # Admin bot has the flag cookie
                ctx.add_cookies([{
                    "name": "session",
                    "value": "ADMIN_SECRET_TOKEN",
                    "domain": "localhost",
                    "path": "/",
                }])
                page = ctx.new_page()
                # Visit the reported URL — JS executes here (fetch, Image, etc.)
                page.goto(target, wait_until="networkidle", timeout=15000)
                # Give async JS payloads time to complete their outbound requests
                time.sleep(5)
                page.close()
                browser.close()
        except Exception as e:
            print(f"[bot] error: {e}")

    threading.Thread(target=bot_visit, args=(url,), daemon=True).start()
    return "Report submitted. Admin will review shortly."

@app.route("/flag")
def flag():
    cookie = request.cookies.get("session", "")
    if cookie == "ADMIN_SECRET_TOKEN":
        return FLAG
    return "Forbidden — admin only", 403

if __name__ == "__main__":
    print(f"[*] XSS target running at http://localhost:7331")
    print(f"[*] Flag: {FLAG}  (only accessible with admin session cookie)")
    app.run(host="0.0.0.0", port=7331, debug=False)
