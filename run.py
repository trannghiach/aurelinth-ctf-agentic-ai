# run.py
import sys
import time
import threading
from datetime import datetime
from memory import get_mongo, get_redis
from orchestrator.core import Orchestrator, TaskStatus
from orchestrator.queue import TaskQueue
from orchestrator.ai_planner import plan_campaign
from teams.ctf_web.team import build_prompt


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def spinner(label: str, stop_event: threading.Event) -> None:
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not stop_event.is_set():
        elapsed = int(time.time() - stop_event.start_time)
        print(f"\r  {frames[i % len(frames)]} [{label}] running... {elapsed}s", end="", flush=True)
        i += 1
        time.sleep(0.1)
    print(f"\r", end="")


def run_task_with_spinner(orc, task, prompt) -> None:
    stop = threading.Event()
    stop.start_time = time.time()
    t = threading.Thread(target=spinner, args=(task.agent_type.value, stop))
    t.start()
    try:
        orc.run_task(task, prompt)
    finally:
        stop.set()
        t.join()


def run_pipeline(target: str, notes: str = "") -> None:
    db = get_mongo()
    r = get_redis()
    q = TaskQueue(r)
    orc = Orchestrator(q, db)

    print(f"\n{'='*60}")
    print(f"  AURELINTH — {ts()}")
    print(f"  Target : {target}")
    print(f"  Notes  : {notes or 'none'}")
    print(f"{'='*60}\n")

    print(f"[{ts()}] Planning campaign with AI...")
    tasks = plan_campaign(target, notes)
    print(f"[{ts()}] Pipeline: {len(tasks)} tasks\n")
    for t in tasks:
        deps = t.depends_on if t.depends_on else ["—"]
        print(f"  {t.agent_type.value:22} id={t.id}  deps={deps}")

    print()
    total_start = time.time()

    for task in tasks:
        if task.is_terminal():
            continue

        # Wait for dependencies
        wait_logged = False
        while not task.can_run(q.get_completed_ids()):
            if not wait_logged:
                print(f"[{ts()}] ⏸  [{task.agent_type.value}] waiting for dependencies...")
                wait_logged = True
            time.sleep(2)

        orc.tasks[task.id] = task
        context = orc.get_context_for(task)
        prompt = build_prompt(task.agent_type, target, context)

        task_start = time.time()
        print(f"[{ts()}] →  [{task.agent_type.value}] starting")

        run_task_with_spinner(orc, task, prompt)

        elapsed = int(time.time() - task_start)

        if task.status == TaskStatus.DONE:
            summary = task.result.get("summary", "")[:150].replace("\n", " ")
            print(f"[{ts()}] ✓  [{task.agent_type.value}] done in {elapsed}s")
            print(f"           └─ {summary}...")
        elif task.status == TaskStatus.FAILED:
            print(f"[{ts()}] ✗  [{task.agent_type.value}] failed after {elapsed}s — continuing")

        print()

    total = int(time.time() - total_start)
    done   = [t for t in tasks if t.status == TaskStatus.DONE]
    failed = [t for t in tasks if t.status == TaskStatus.FAILED]

    print(f"{'='*60}")
    print(f"  COMPLETE — {ts()} — total {total}s")
    print(f"  Done: {len(done)}/{len(tasks)}  Failed: {len(failed)}/{len(tasks)}")
    print(f"{'='*60}\n")

    for task in tasks:
        if task.agent_type.value == "flag_extractor" and task.result:
            print("FINAL REPORT:")
            print("─"*60)
            print(task.result.get("summary", "No output"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <target> [notes]")
        sys.exit(1)

    target = sys.argv[1]
    notes  = sys.argv[2] if len(sys.argv) > 2 else ""
    run_pipeline(target, notes)