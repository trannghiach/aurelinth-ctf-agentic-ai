# Aurelinth — Claude Code Instructions

## RULE 1 — NO HARDCODING (highest priority, no exceptions)

**Never hardcode specific values in skills, references, or agent prompts.**

This means:
- No specific endpoint paths (`/api/flag`, `/api/profile`, `/api/admin`)
- No specific parameter names (`bio=`, `username=`, `bookingId=`)
- No specific field names from a particular app (`users.secret`, `notes.content`)
- No specific URL patterns enumerated as examples (`/note/1`, `/post/2`)
- No specific payloads tied to one app's structure

**What to write instead:**
- Decision logic and principles — "identify writable fields in the response, write to one, read it back"
- Reasoning frameworks — "find the per-item link in the listing HTML, that's the display URL"
- Adaptive patterns — "probe any admin/restricted endpoints returned in the recon context"

Skills are reusable across every CTF challenge. The moment a specific endpoint or field name appears, the skill becomes brittle and only works on one target. The agent reads the app — the skill gives it the reasoning framework, not the answer.

**This rule applies to: SKILL.md files, references/*.md files, assets/*.md files, any prompt injected into an agent.**
