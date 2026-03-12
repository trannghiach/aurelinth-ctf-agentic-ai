# Aurelinth — Orchestrator core logic: task management, dependency resolution, context building, and agent execution.
import uuid
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from orchestrator.gemini import call
from orchestrator.queue import TaskQueue
from orchestrator.context import serialize, build_prompt_context


class TaskStatus(Enum):
    PENDING  = "pending"
    RUNNING  = "running"
    DONE     = "done"
    FAILED   = "failed"
    BLOCKED  = "blocked"


class AgentType(Enum):
    WEB_RECON          = "web_recon"
    SQLI_HUNTER        = "sqli_hunter"
    XSS_HUNTER         = "xss_hunter"
    AUTH_BYPASSER      = "auth_bypasser"
    LFI_HUNTER         = "lfi_hunter"
    SSTI_HUNTER        = "ssti_hunter"
    IDOR_HUNTER        = "idor_hunter"
    FILE_UPLOAD_HUNTER = "file_upload_hunter"
    FLAG_EXTRACTOR     = "flag_extractor"


@dataclass
class Task:
    id:          str
    agent_type:  AgentType
    target:      str
    depends_on:  list[str] = field(default_factory=list)
    status:      TaskStatus = TaskStatus.PENDING
    result:      Optional[dict] = None
    retries:     int = 0
    MAX_RETRIES: int = 2

    def can_run(self, completed_ids: set[str]) -> bool:
        return all(dep in completed_ids for dep in self.depends_on)

    def is_terminal(self) -> bool:
        return self.status in {TaskStatus.DONE, TaskStatus.FAILED}


def make_id() -> str:
    return str(uuid.uuid4())[:8]


def scan_flag(text: str, flag_format: str) -> str | None:
    r"""..."""
    if not flag_format or not text:
        return None
    prefix = flag_format.split("{")[0]
    pattern = re.escape(prefix) + r"\{[^}]+\}"
    matches = re.findall(pattern, text)  # ← fix: define matches
    real = [m for m in matches if m != flag_format and "..." not in m]
    return real[0] if real else None


def scan_unexpected(summary: str) -> dict | None:
    """
    Scan agent output for off-scope findings.
    Returns dict if UNEXPECTED section found.
    """
    if "UNEXPECTED:" not in summary:
        return None
    try:
        section = summary.split("UNEXPECTED:")[1].split("\n\n")[0]
        return {"raw": section.strip()}
    except Exception:
        return None


class Orchestrator:
    def __init__(self, queue: TaskQueue, db):
        self.q        = queue
        self.db       = db
        self.tasks:    dict[str, Task] = {}
        self.contexts: dict[str, dict] = {}

    def run_task(self, task: Task, prompt: str,
                 flag_format: str = "") -> str | None:
        """
        Run a single task. Returns flag string if found, None otherwise.
        """
        completed = self.q.get_completed_ids()
        if not task.can_run(completed):
            task.status = TaskStatus.BLOCKED
            return None

        task.status = TaskStatus.RUNNING
        self.q.emit("agent_start", {
            "task_id": task.id,
            "agent":   task.agent_type.value
        })

        try:
            raw = call(
                task.agent_type.value,
                prompt,
                task_id=task.id,
                emit_fn=self.q.emit
            )
            ctx = serialize(task.id, task.agent_type.value, raw, self.db)
            self.contexts[task.id] = ctx

            task.result = ctx
            task.status = TaskStatus.DONE
            self.q.mark_done(task.id)
            self.q.emit("agent_done", {
                "task_id":   task.id,
                "truncated": ctx["truncated"]
            })

            # Scan for flag
            flag = scan_flag(raw, flag_format)
            if flag:
                self.q.emit("flag_found", {
                    "task_id": task.id,
                    "agent":   task.agent_type.value,
                    "flag":    flag
                })
                return flag

            # Scan for unexpected findings
            unexpected = scan_unexpected(ctx.get("summary", ""))
            if unexpected:
                self.q.emit("unexpected_finding", {
                    "task_id": task.id,
                    "agent":   task.agent_type.value,
                    "finding": unexpected["raw"][:200]
                })

            return None

        except Exception as e:
            task.retries += 1
            # Always mark FAILED — supervisor loop not to handle retry
            task.status = TaskStatus.FAILED
            self.q.mark_failed(task.id)
            self.q.emit("agent_failed", {
                "task_id": task.id,
                "error":   str(e)[:200]
            })
            # Save empty context for the next agent not to be None
            self.contexts[task.id] = {
                "mongo_ref": None,
                "summary":   f"[FAILED: {str(e)[:100]}]",
                "truncated": False,
            }
            return None

    def get_context_for(self, task: Task) -> str:
        dep_contexts = []
        for dep_id in task.depends_on:
            if dep_id in self.contexts:
                ctx = self.contexts[dep_id].copy()
                ctx["agent_type"] = self.tasks[dep_id].agent_type.value
                dep_contexts.append(ctx)
        return build_prompt_context(dep_contexts)