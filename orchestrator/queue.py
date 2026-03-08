#Aurelinth - Redis Task Queue

import json
from redis import Redis

class TaskQueue:
    def __init__(self, redis: Redis):
        self.r = redis
        self.QUEUE_KEY = "aurelinth:tasks:pending"
        self.RUNNING_KEY = "aurelinth:tasks:running"
        
    def enqueue(self, task) -> None:
        payload = {
            "id": task.id,
            "agent_type": task.agent_type.value,
            "target": task.target,
            "depends_on": task.depends_on,
            "retries": task.retries
        }
        self.r.lpush(self.QUEUE_KEY, json.dumps(payload))
        
    def dequeue(self) -> dict | None:
        raw = self.r.rpop(self.QUEUE_KEY)
        if raw:
            return json.loads(raw)
        return None
    
    def mark_done(self, task_id: str) -> None:
        self.r.sadd("aurelinth:tasks:done", task_id)
        
    def mark_failed(self, task_id: str) -> None:
        self.r.sadd("aurelinth:tasks:failed", task_id)
        
    def get_completed_ids(self) -> set[str]:
        return self.r.smembers("aurelinth:tasks:done")
    
    def emit(self, event_type: str, data: dict) -> None:
        """
        Fire an event to Redis Stream -> Monitor UI will receive through SSE later
        """
        self.r.xadd("aurelinth:events", {"type": event_type, "data": json.dumps(data)})