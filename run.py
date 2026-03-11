# Aurelinth — Main runner script: runs the pipeline for a given target, manages phases, and prints final report.
import sys
import time
import threading
from datetime import datetime
from memory import get_mongo, get_redis
from orchestrator.core import Orchestrator, Task, AgentType, TaskStatus, make_id, scan_flag
from orchestrator.queue import TaskQueue
from orchestrator.supervisor import decide
from teams.ctf_web.team import build_prompt


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def spinner(label: str, stop_event: threading.Event) -> None:
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    i = 0
    while not stop_event.is_set():
        elapsed = int(time.time() - stop_event.start_time)
        print(f"\r  {frames[i%len(frames)]} [{label}] {elapsed}s", end="", flush=True)
        i += 1
        time.sleep(0.1)
    print(f"\r", end="")


def run_agent(orc: Orchestrator, agent_type: AgentType, target: str,
              flag_format: str, dep_ids: list[str]) -> tuple[Task, str | None]:
    """Run a single agent, return (task, flag_or_None)."""
    task = Task(
        id=make_id(),
        agent_type=agent_type,
        target=target,
        depends_on=dep_ids
    )
    orc.tasks[task.id] = task

    context = orc.get_context_for(task)
    prompt  = build_prompt(agent_type, target, context, flag_format)

    stop = threading.Event()
    stop.start_time = time.time()
    t = threading.Thread(target=spinner, args=(agent_type.value, stop))
    t.start()

    try:
        flag = orc.run_task(task, prompt, flag_format=flag_format)
    finally:
        stop.set()
        t.join()

    elapsed = int(time.time() - stop.start_time)
    if task.status == TaskStatus.DONE:
        summary = (task.result or {}).get("summary", "")[:150].replace("\n", " ")
        print(f"[{ts()}] ✓  [{agent_type.value}] done in {elapsed}s")
        print(f"           └─ {summary}")
    elif task.status == TaskStatus.FAILED:
        print(f"[{ts()}] ✗  [{agent_type.value}] failed after {elapsed}s")
    print()

    return task, flag


def run_pipeline(target: str, notes: str = "", flag_format: str = "") -> None:
    db = get_mongo()
    r  = get_redis()
    q  = TaskQueue(r)
    orc = Orchestrator(q, db)

    print(f"\n{'='*60}")
    print(f"  AURELINTH — {ts()}")
    print(f"  Target      : {target}")
    print(f"  Notes       : {notes or 'none'}")
    print(f"  Flag format : {flag_format or 'unknown'}")
    print(f"{'='*60}\n")

    total_start  = time.time()
    already_ran  = set()
    completed    = []   # [{"agent": ..., "summary": ...}]
    unexpected   = []   # [{"agent": ..., "finding": ...}]
    found_flag   = None
    last_task_id = None

    # --- Phase 1: web_recon always first ---
    print(f"[{ts()}] Phase 1 — web_recon\n")
    recon_task, flag = run_agent(
        orc, AgentType.WEB_RECON, target, flag_format, []
    )
    already_ran.add("web_recon")
    last_task_id = recon_task.id

    if recon_task.status == TaskStatus.DONE:
        summary = (recon_task.result or {}).get("summary", "")
        completed.append({"agent": "web_recon", "summary": summary})
        if flag:
            found_flag = flag

    # --- Phase 2: Supervisor loop ---
    iteration = 0
    while not found_flag:
        iteration += 1
        print(f"[{ts()}] Supervisor — iteration {iteration}")

        decision = decide(
            target=target,
            flag_format=flag_format,
            completed=completed,
            unexpected=unexpected,
            already_ran=already_ran,
        )

        q.emit("supervisor_decision", {
            "iteration": iteration,
            "next":      decision.get("next"),
            "reason":    decision.get("reason", ""),
            "stop":      decision.get("stop", False),
        })

        print(f"           next={decision.get('next')} | {decision.get('reason', '')}")
        print()

        # Check if supervisor found flag in context
        if decision.get("flag"):
            found_flag = decision["flag"]
            break

        # Stop condition
        if decision.get("stop") or not decision.get("next"):
            break

        next_agent_str = decision["next"]
        try:
            next_agent = AgentType(next_agent_str)
        except ValueError:
            print(f"[{ts()}] ✗  Unknown agent '{next_agent_str}' — stopping")
            break

        # Run next agent with recon as context
        task, flag = run_agent(
            orc, next_agent, target, flag_format, [last_task_id]
        )
        already_ran.add(next_agent_str)
        last_task_id = task.id

        if task.status == TaskStatus.DONE:
            summary = (task.result or {}).get("summary", "")
            completed.append({"agent": next_agent_str, "summary": summary})

            # Check unexpected findings
            from orchestrator.core import scan_unexpected
            unexp = scan_unexpected(summary)
            if unexp:
                unexpected.append({"agent": next_agent_str, "finding": unexp["raw"]})

            if flag:
                found_flag = flag
                break

    # --- Phase 3: flag_extractor if no flag yet ---
    if not found_flag:
        print(f"[{ts()}] Phase 3 — flag_extractor\n")
        all_dep_ids = [t.id for t in orc.tasks.values()
                       if t.status == TaskStatus.DONE]

        flag_task = Task(
            id=make_id(),
            agent_type=AgentType.FLAG_EXTRACTOR,
            target=target,
            depends_on=all_dep_ids
        )
        orc.tasks[flag_task.id] = flag_task

        # Build full context from all completed agents
        full_context = "\n".join(
            f"- [{c['agent']}]: {c['summary'][:500]}" for c in completed
        )
        prompt = build_prompt(
            AgentType.FLAG_EXTRACTOR, target,
            f"## Context from all agents:\n{full_context}",
            flag_format
        )

        stop = threading.Event()
        stop.start_time = time.time()
        t = threading.Thread(target=spinner, args=("flag_extractor", stop))
        t.start()
        try:
            found_flag = orc.run_task(flag_task, prompt, flag_format=flag_format)
        finally:
            stop.set()
            t.join()

        elapsed = int(time.time() - stop.start_time)
        if flag_task.status == TaskStatus.DONE:
            print(f"[{ts()}] ✓  [flag_extractor] done in {elapsed}s\n")
        else:
            print(f"[{ts()}] ✗  [flag_extractor] failed after {elapsed}s\n")

    # --- Final report ---
    total = int(time.time() - total_start)
    done   = [t for t in orc.tasks.values() if t.status == TaskStatus.DONE]
    failed = [t for t in orc.tasks.values() if t.status == TaskStatus.FAILED]

    print(f"{'='*60}")
    print(f"  COMPLETE — {ts()} — total {total}s")
    print(f"  Agents run : {len(orc.tasks)}")
    print(f"  Done/Failed: {len(done)}/{len(failed)}")
    if found_flag:
        print(f"  FLAG       : {found_flag}")
    print(f"{'='*60}\n")

    # Print flag_extractor report if available
    for task in orc.tasks.values():
        if task.agent_type == AgentType.FLAG_EXTRACTOR and task.result:
            print("FINAL REPORT:")
            print("─"*60)
            print(task.result.get("summary", "No output"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <target> [notes] [flag_format]")
        print("Example: python run.py http://... 'php app' 'picoCTF{...}'")
        sys.exit(1)

    target      = sys.argv[1]
    notes       = sys.argv[2] if len(sys.argv) > 2 else ""
    flag_format = sys.argv[3] if len(sys.argv) > 3 else ""
    run_pipeline(target, notes, flag_format)