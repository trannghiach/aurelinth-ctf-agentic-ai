# Web Recon Output Template

Fill every field below. Write "N/A" for fields with no data. Do NOT omit any marker.
Do NOT add narrative text, raw HTML, or tool banners outside the markers.

---

TECHNOLOGY:
- Server: [e.g. nginx/1.19.0]
- Language: [e.g. PHP/5.6.40]
- Framework: [e.g. Laravel 8.x or unknown]
- IP: [IP address]
- CDN: [provider or none]

ENDPOINTS:
- [METHOD  /path  — notes: form fields, params, auth state, vuln hints]
- [repeat per discovered endpoint]

INPUTS:
- [/route → param_name (type), e.g. "GET param, reflected in response"]
- [Cookie: name=value — e.g. "JWT-looking blob"]
- [repeat per input]

INJECTION:
- endpoint: [METHOD /path or N/A]
- params: [field names observed in the request, e.g. "email, password" or N/A]
- db: [MySQL / PostgreSQL / SQLite / MongoDB / unknown]
- type: [sql-error / boolean-difference / array-injection / operator-injection / reflected-xss / stored-xss / ssti / lfi / unknown]
- signal: [exact observed difference, e.g. "302 redirect when PARAM[]=.* sent vs 200 on normal", or "syntax error in body", or N/A]
- confirmed: [YES if a distinct signal was observed / SUSPECTED if no signal yet]

UNEXPECTED:
- [Interesting findings not fitting above: exposed files, credentials in pages, error disclosures]
- [Or N/A]

RECOMMENDED NEXT: [single agent name]
- Reason: [one sentence citing exact evidence from tool output, e.g. "/search?q= reflects input unencoded, admin bot at /report"]
