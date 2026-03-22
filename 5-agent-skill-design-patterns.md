# 5 Agent Skill Design Patterns Every ADK Developer Should Know

> Originally by Google Cloud Tech. Rewritten with LLM-readable diagrams replacing all images.

---

## The Problem: Format Is Solved, Content Design Is Not

When it comes to `SKILL.md`, developers tend to fixate on the format—getting the YAML right, structuring directories, and following the spec. But with more than 30 agent tools (like Claude Code, Gemini CLI, and Cursor) standardizing on the same layout, the formatting problem is practically obsolete.

The challenge now is **content design**. The specification explains how to package a skill, but offers zero guidance on how to structure the logic inside it. For example, a skill that wraps FastAPI conventions operates completely differently from a four-step documentation pipeline, even though their `SKILL.md` files look identical on the outside.

By studying how skills are built across the ecosystem—from Anthropic's repositories to Vercel and Google's internal guidelines—five recurring design patterns emerge. Each one answers a different architectural question.

---

## Pattern 1: Tool Wrapper

**Core question:** *"How do I teach my agent a specific library or framework?"*

A Tool Wrapper gives your agent on-demand context for a specific library. Instead of hardcoding API conventions into your system prompt, you package them into a skill. Your agent only loads this context when it actually works with that technology. It is the simplest pattern to implement.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      AGENT RUNTIME                      │
│                                                         │
│  ┌─────────────┐    trigger     ┌────────────────────┐  │
│  │  User        │──────────────▶│  SKILL.md           │  │
│  │  Request     │  "write a     │  (Tool Wrapper)     │  │
│  │              │   FastAPI     │                     │  │
│  └─────────────┘   endpoint"   │  Instructions:      │  │
│                                 │  "Load conventions  │  │
│                                 │   when reviewing    │  │
│                                 │   or writing code"  │  │
│                                 └────────┬───────────┘  │
│                                          │              │
│                                   load on demand        │
│                                          │              │
│                                          ▼              │
│                                 ┌────────────────────┐  │
│                                 │  references/        │  │
│                                 │  conventions.md     │  │
│                                 │                     │  │
│                                 │  • Route patterns   │  │
│                                 │  • Dependency       │  │
│                                 │    injection        │  │
│                                 │  • Response models  │  │
│                                 │  • Error handling   │  │
│                                 └────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Example SKILL.md

```yaml
---
name: fastapi-conventions
description: Teaches the agent FastAPI project conventions.
---
```

```markdown
# Instructions

When the user asks you to review or write FastAPI code,
load references/conventions.md first.

Apply the conventions to all generated code.
Do NOT deviate from the patterns in that file.
```

The instructions explicitly tell the agent to load the `conventions.md` file **only when** it starts reviewing or writing code. The context stays out of the prompt until needed.

---

## Pattern 2: Generator

**Core question:** *"How do I guarantee consistent output every time?"*

While the Tool Wrapper applies knowledge, the Generator enforces consistent output. If you struggle with an agent generating different document structures on every run, the Generator solves this by orchestrating a fill-in-the-blank process.

It leverages two optional directories: `assets/` holds your output template, and `references/` holds your style guide. The instructions act as a project manager. They tell the agent to load the template, read the style guide, ask the user for missing variables, and populate the document.

### Flow

```
  ┌──────────────┐
  │  SKILL.md    │    Acts as the "project manager"
  │  (Generator) │    coordinating all steps
  └──────┬───────┘
         │
         ├──────────────────────────────────────┐
         │                                      │
         ▼                                      ▼
  ┌──────────────────┐               ┌──────────────────┐
  │  assets/          │               │  references/      │
  │  template.md      │               │  style-guide.md   │
  │                   │               │                   │
  │  "## {{TITLE}}    │               │  • Tone: formal   │
  │   Author: {{…}}   │               │  • Max 2000 words  │
  │   ---             │               │  • Use active      │
  │   {{BODY}}"       │               │    voice           │
  └──────────────────┘               └──────────────────┘
         │                                      │
         └──────────────┬───────────────────────┘
                        │
                        ▼
              ┌───────────────────┐
              │  Agent asks user   │
              │  for missing       │
              │  variables:        │
              │                    │
              │  • TITLE = ?       │
              │  • AUTHOR = ?      │
              │  • BODY context?   │
              └────────┬──────────┘
                       │
                       ▼
              ┌───────────────────┐
              │  Populated Output  │
              │  (consistent       │
              │   structure every  │
              │   single time)     │
              └───────────────────┘
```

This is practical for generating predictable API documentation, standardizing commit messages, or scaffolding project architectures. The output structure never drifts because the template is the source of truth, not the LLM's improvisation.

---

## Pattern 3: Pipeline

**Core question:** *"How do I enforce a strict multi-step workflow?"*

For complex tasks, you cannot afford skipped steps or ignored instructions. The Pipeline pattern enforces a strict, sequential workflow with hard checkpoints. The instructions themselves serve as the workflow definition.

By implementing explicit **diamond gate conditions** (such as requiring user approval before moving from docstring generation to final assembly), the Pipeline ensures an agent cannot bypass a complex task and present an unvalidated final result.

### Execution Flow

```
 ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
 │  STEP 1  │     │  STEP 2  │     │  STEP 3  │     │  STEP 4  │
 │          │     │          │     │          │     │          │
 │  Parse   │────▶│  Extract │────▶│  Generate │────▶│  Assemble│
 │  source  │     │  doc-    │     │  doc-     │     │  final   │
 │  code    │     │  strings │     │  strings  │     │  output  │
 └──────────┘     └─────┬────┘     └─────┬─────┘     └──────────┘
                        │                │
                   ┌────┴────┐      ┌────┴────┐
                   │  GATE   │      │  GATE   │
                   │         │      │         │
                   │ Load    │      │ User    │
                   │ refs/   │      │ MUST    │
                   │ api-    │      │ confirm │
                   │ style   │      │ before  │
                   │ .md     │      │ proceed │
                   └─────────┘      └─────────┘

 KEY RULE: The agent is FORBIDDEN from jumping to Step 4
 until Step 3's gate condition (user approval) is satisfied.
```

### Example SKILL.md

```yaml
---
name: doc-pipeline
description: Four-step documentation generation pipeline.
---
```

```markdown
# Step 1 — Parse
Scan the source code. Identify all public functions.

# Step 2 — Extract
Load references/api-style.md.
Generate a docstring for each function.

# Step 3 — Review
Present all docstrings to the user.
⛔ DO NOT proceed to Step 4 until the user confirms.

# Step 4 — Assemble
Load assets/doc-template.md.
Populate the template with confirmed docstrings.
Deliver the final document.
```

This pattern utilizes all optional directories, pulling in different reference files and templates only at the specific step where they are needed, keeping the context window clean.

---

## Pattern 4: Reviewer

**Core question:** *"How do I build a reusable quality gate?"*

The Reviewer pattern separates **what to check** from **how to check it**. Rather than writing a long system prompt detailing every code smell, you store a modular rubric inside a `references/review-checklist.md` file. When a user submits code, the agent loads this checklist and methodically scores the submission, grouping its findings by severity.

### Architecture

```
                      ┌───────────────────────┐
                      │      SKILL.md         │
                      │      (Reviewer)       │
                      │                       │
                      │  "Load the checklist. │
                      │   Score each item.    │
                      │   Group by severity." │
                      └───────────┬───────────┘
                                  │
                           load on demand
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │  references/           │
                      │  review-checklist.md   │
                      └───────────┬───────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
   │  SWAP: Python  │   │  SWAP: OWASP   │   │  SWAP: a11y    │
   │  style guide   │   │  security      │   │  compliance    │
   │                │   │  checklist     │   │  checklist     │
   │  → Code review │   │  → Security    │   │  → Accessibil- │
   │    agent       │   │    audit agent │   │    ity audit   │
   └────────────────┘   └────────────────┘   └────────────────┘

 SAME skill infrastructure, DIFFERENT checklists
 = completely different specialized audits
```

### Example SKILL.md

```yaml
---
name: code-reviewer
description: Reviews code against a modular checklist.
---
```

```markdown
# Instructions

When the user submits code for review:

1. Load references/review-checklist.md
2. Evaluate every item in the checklist
3. Group findings by severity:
   🔴 Critical  — must fix before merge
   🟡 Warning   — should fix, not blocking
   🟢 Nit       — optional improvements
4. Output a structured report
```

If you swap out a Python style checklist for an OWASP security checklist, you get a completely different, specialized audit using the exact same skill infrastructure. It is a highly effective way to automate PR reviews or catch vulnerabilities before a human looks at the code.

---

## Pattern 5: Inversion

**Core question:** *"How do I stop the agent from guessing and force it to gather context first?"*

Agents inherently want to guess and generate immediately. The Inversion pattern flips this dynamic. Instead of the user driving the prompt and the agent executing, **the agent acts as an interviewer**.

Inversion relies on explicit, non-negotiable gating instructions (like "DO NOT start building until all phases are complete") to force the agent to gather context first. It asks structured questions sequentially and waits for your answers before moving to the next phase. The agent refuses to synthesize a final output until it has a complete picture of your requirements and deployment constraints.

### Traditional vs. Inversion Flow

```
  TRADITIONAL FLOW (user drives):
  ════════════════════════════════════════════════════════
  User ──prompt──▶ Agent ──generates──▶ Output (often wrong)


  INVERSION FLOW (agent drives):
  ════════════════════════════════════════════════════════

  User: "Build me a project"
    │
    ▼
  ┌──────────────────────────────────────────────────┐
  │                    AGENT                          │
  │                                                   │
  │  Phase 1: REQUIREMENTS                            │
  │  ├─ "What is the target platform?"                │
  │  ├─ "What language / framework?"                  │
  │  └─ "Who is the end user?"                        │
  │       │                                           │
  │       ▼  ⛔ GATE: all Phase 1 answers received    │
  │                                                   │
  │  Phase 2: CONSTRAINTS                             │
  │  ├─ "What is the deployment target?"              │
  │  ├─ "Any performance requirements?"               │
  │  └─ "Auth strategy?"                              │
  │       │                                           │
  │       ▼  ⛔ GATE: all Phase 2 answers received    │
  │                                                   │
  │  Phase 3: SYNTHESIS                               │
  │  └─ Agent now has complete context                 │
  │     → Generates informed, validated output         │
  └──────────────────────────────────────────────────┘

 KEY INSTRUCTION: "DO NOT start building until
 ALL phases are complete."
```

This eliminates the #1 failure mode: the agent confidently generating the wrong thing because it assumed what you wanted.

---

## Combining Patterns

These patterns are not mutually exclusive. They compose naturally:

- A **Pipeline** skill can include a **Reviewer** step at the end to double-check its own work.
- A **Generator** can rely on **Inversion** at the very beginning to gather the necessary variables before filling out its template.

```
  ┌─────────────────────────────────────────────────────────┐
  │               COMPOSED SKILL EXAMPLE                    │
  │                                                         │
  │  ┌────────────┐   ┌────────────┐   ┌────────────────┐  │
  │  │ INVERSION  │──▶│ GENERATOR  │──▶│   REVIEWER     │  │
  │  │            │   │            │   │                 │  │
  │  │ Gather all │   │ Fill the   │   │ Score output   │  │
  │  │ variables  │   │ template   │   │ against        │  │
  │  │ via Q&A    │   │ with       │   │ checklist      │  │
  │  │            │   │ collected  │   │                 │  │
  │  │            │   │ data       │   │ Pass? ──▶ Done │  │
  │  │            │   │            │   │ Fail? ──▶ Loop │  │
  │  └────────────┘   └────────────┘   └────────────────┘  │
  └─────────────────────────────────────────────────────────┘
```

Thanks to ADK's `SkillToolset` and progressive disclosure, your agent only spends context tokens on the exact patterns it needs at runtime.

---

## Quick Reference

| Pattern | Core Question | Key Mechanism |
|---|---|---|
| **Tool Wrapper** | How do I teach my agent a library? | On-demand `references/` loading |
| **Generator** | How do I guarantee consistent output? | Template in `assets/` + style guide in `references/` |
| **Pipeline** | How do I enforce a multi-step workflow? | Sequential steps with explicit gate conditions |
| **Reviewer** | How do I build a reusable quality gate? | Swappable checklists in `references/` |
| **Inversion** | How do I force context-gathering first? | Agent-as-interviewer with non-negotiable gates |

---

## The Skill File Structure

All five patterns operate within the same standardized directory layout. What changes between patterns is how the instructions reference and orchestrate these files:

```
my-skill/
├── SKILL.md              ← Required. YAML frontmatter + instructions.
│                            This is where the pattern logic lives.
│
├── references/           ← Optional. Loaded on demand.
│   ├── conventions.md       (Tool Wrapper: API conventions)
│   ├── style-guide.md       (Generator: writing rules)
│   ├── review-checklist.md  (Reviewer: scoring rubric)
│   └── api-style.md         (Pipeline: step-specific reference)
│
└── assets/               ← Optional. Templates & structured data.
    ├── template.md          (Generator: output skeleton)
    └── doc-template.md      (Pipeline: final assembly template)
```

---

## Conclusion

Stop trying to cram complex and fragile instructions into a single system prompt. Break your workflows down, apply the right structural pattern, and build reliable agents.

The Agent Skills specification is open-source and natively supported across ADK. You already know how to package the format. **Now you know how to design the content.**