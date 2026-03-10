# Aurelinth - Core data structures and logic for task management, context serialization, and Gemini interaction.

import uuid

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from orchestrator.gemini import call
from orchestrator.queue import TaskQueue
from orchestrator.context import serialize, build_prompt_context

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"
    
class AgentType(Enum):
    WEB_RECON = "web_recon"
    SQLI_HUNTER = "sqli_hunter"
    XSS_HUNTER = "xss_hunter"
    AUTH_BYPASSER = "auth_bypasser"
    FLAG_EXTRACTOR = "flag_extractor"
    
@dataclass
class Task:
    id: str
    agent_type: AgentType
    target: str
    depends_on: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict] = None
    retries: int = 0
    MAX_RETRIES: int = 2
    
    def can_run(self, completed_ids: set[str]) -> bool:
        return all(dep in completed_ids for dep in self.depends_on)
    
    def is_terminal(self) -> bool:
        return self.status in {TaskStatus.DONE, TaskStatus.FAILED}
    
def make_id() -> str:
    return str(uuid.uuid4())[:8]

def default_ctf_pipeline(target: str) -> list[Task]:
    t_recon = Task(id=make_id(), agent_type=AgentType.WEB_RECON, target=target)
    t_sqli  = Task(id=make_id(), agent_type=AgentType.SQLI_HUNTER, target=target, depends_on=[t_recon.id])
    t_xss   = Task(id=make_id(), agent_type=AgentType.XSS_HUNTER, target=target, depends_on=[t_recon.id])
    t_auth  = Task(id=make_id(), agent_type=AgentType.AUTH_BYPASSER, target=target, depends_on=[t_recon.id])
    t_flag  = Task(id=make_id(), agent_type=AgentType.FLAG_EXTRACTOR, target=target,
                   depends_on=[t_sqli.id, t_xss.id, t_auth.id])
    return [t_recon, t_sqli, t_xss, t_auth, t_flag]

class Orchestrator:
    def __init__(self, queue: TaskQueue, db):
        self.queue = queue
        self.db = db
        self.tasks: dict[str, Task] = {}
        self.contexts: dict[str, dict] = {}  # task_id -> context
        
    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task
        self.queue.enqueue(task)
        
    def run_task(self, task: Task, prompt: str) -> None:
        """
        Run a single task: call Gemini, serialize context, emit event.
        """
        completed = self.queue.get_completed_ids()
        
        if not task.can_run(completed):
            task.status = TaskStatus.BLOCKED
            return
        
        task.status = TaskStatus.RUNNING
        self.queue.emit("agent_start", {"task_id": task.id, "agent": task.agent_type.value})
        
        try:
            raw = call(task.agent_type.value, prompt)
            ctx = serialize(task.id, task.agent_type.value, raw, self.db)
            self.contexts[task.id] = ctx
            
            task.result = ctx
            task.status = TaskStatus.DONE
            self.queue.mark_done(task.id)
            self.queue.emit("agent_done", {"task_id": task.id, "truncated": ctx["truncated"]})
            
        except Exception as e:
            task.retries += 1
            if task.retries >= task.MAX_RETRIES:
                task.status = TaskStatus.FAILED
                self.queue.mark_failed(task.id)
                self.queue.emit("agent_failed", {"task_id": task.id, "error": str(e)[:200]})
            else:
                task.status = TaskStatus.PENDING
                self.queue.enqueue(task)  # Retry by re-enqueueing
                
    def get_context_for(self, task: Task) -> str:
        """
        Get context from all task's dependencies.
        """
        dep_contexts = []
        for dep_id in task.depends_on:
            if dep_id in self.contexts:
                ctx = self.contexts[dep_id].copy()
                ctx["agent_type"] = self.tasks[dep_id].agent_type.value
                dep_contexts.append(ctx)
        return build_prompt_context(dep_contexts)
        
        