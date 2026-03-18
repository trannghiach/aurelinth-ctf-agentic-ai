# Aurelinth — Orchestrator core logic: task management, dependency resolution, context building, and agent execution.
import uuid
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
    # --- Blackbox agents ---
    WEB_RECON          = "web_recon"
    SQLI_HUNTER        = "sqli_hunter"
    XSS_HUNTER         = "xss_hunter"
    AUTH_BYPASSER      = "auth_bypasser"
    LFI_HUNTER         = "lfi_hunter"
    SSTI_HUNTER        = "ssti_hunter"
    IDOR_HUNTER        = "idor_hunter"
    CRYPTO_HUNTER      = "crypto_hunter"
    FILE_UPLOAD_HUNTER = "file_upload_hunter"
    FLAG_EXTRACTOR     = "flag_extractor"

    # --- Whitebox infrastructure ---
    CODE_READER        = "code_reader"
    DEP_CHECKER        = "dep_checker"
    VULN_REASONER      = "vuln_reasoner"

    # --- Whitebox auditors (mirror blackbox hunters) ---
    SQLI_AUDITOR             = "sqli_auditor"
    XSS_AUDITOR              = "xss_auditor"
    AUTH_AUDITOR             = "auth_auditor"
    LFI_AUDITOR              = "lfi_auditor"
    SSTI_AUDITOR             = "ssti_auditor"
    ACCESS_CONTROL_AUDITOR   = "access_control_auditor"
    UPLOAD_AUDITOR           = "upload_auditor"
    RACE_CONDITION_AUDITOR   = "race_condition_auditor"
    CRYPTO_AUDITOR           = "crypto_auditor"
    DESERIALIZATION_AUDITOR  = "deserialization_auditor"


# Agents that belong to whitebox pipeline — used for routing decisions
WHITEBOX_AGENTS = {
    AgentType.CODE_READER,
    AgentType.DEP_CHECKER,
    AgentType.VULN_REASONER,
    AgentType.SQLI_AUDITOR,
    AgentType.XSS_AUDITOR,
    AgentType.AUTH_AUDITOR,
    AgentType.LFI_AUDITOR,
    AgentType.SSTI_AUDITOR,
    AgentType.ACCESS_CONTROL_AUDITOR,
    AgentType.UPLOAD_AUDITOR,
    AgentType.RACE_CONDITION_AUDITOR,
    AgentType.CRYPTO_AUDITOR,
    AgentType.DESERIALIZATION_AUDITOR,
}

WHITEBOX_AUDITORS = WHITEBOX_AGENTS - {
    AgentType.CODE_READER,
    AgentType.DEP_CHECKER,
    AgentType.VULN_REASONER,
}


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


def scan_unexpected(summary: str) -> dict | None:
    """Scan agent output for off-scope findings."""
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

    def run_task(self, task: Task, prompt: str) -> str | None:
        """Run a single task. Returns structured summary or None on failure."""
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
            self.q.emit("agent_done", {"task_id": task.id})

            summary = ctx.get("summary", "")
            unexpected = scan_unexpected(summary)
            if unexpected:
                self.q.emit("unexpected_finding", {
                    "task_id": task.id,
                    "agent":   task.agent_type.value,
                    "finding": unexpected["raw"][:200]
                })

            return summary

        except Exception as e:
            task.retries += 1
            task.status = TaskStatus.FAILED
            self.q.mark_failed(task.id)
            self.q.emit("agent_failed", {
                "task_id": task.id,
                "error":   str(e)[:200]
            })
            self.contexts[task.id] = {
                "mongo_ref": None,
                "summary":   f"[FAILED: {str(e)[:100]}]",
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
