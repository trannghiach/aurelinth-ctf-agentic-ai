# Aurelinth — Main runner script: runs the pipeline for a given target, manages phases, and prints final report.
import sys
import shutil, os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from memory import get_mongo, get_redis
from orchestrator.core import (
    Orchestrator, Task, AgentType, TaskStatus, make_id,
    scan_unexpected,
    WHITEBOX_AUDITORS
)
from orchestrator.queue import TaskQueue
from orchestrator.supervisor import decide
from orchestrator.health import run_health_check
from teams.ctf_web_blackbox.team import build_prompt as build_blackbox_prompt
from teams.ctf_web_whitebox.team import build_prompt as build_whitebox_prompt

MAX_ITERATIONS = 6


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


def run_agent(
    orc: Orchestrator,
    agent_type: AgentType,
    target: str,
    flag_format: str,
    dep_ids: list[str],
    local_target: str | None = None,
    source_code: str | None = None,
    show_spinner: bool = True,
    context_override: str | None = None,
) -> Task:
    """Run a single agent, return the completed Task."""
    task = Task(
        id=make_id(),
        agent_type=agent_type,
        target=target,
        depends_on=dep_ids
    )
    orc.tasks[task.id] = task

    context = context_override if context_override is not None else orc.get_context_for(task)

    if source_code is not None:
        prompt = build_whitebox_prompt(
            agent_type, target, context, flag_format,
            local_target=local_target,
            source_code=source_code,
        )
    else:
        prompt = build_blackbox_prompt(agent_type, target, context, flag_format)

    start_time = time.time()
    if show_spinner:
        stop = threading.Event()
        stop.start_time = start_time
        spinner_thread = threading.Thread(target=spinner, args=(agent_type.value, stop))
        spinner_thread.start()

    try:
        orc.run_task(task, prompt)
    finally:
        if show_spinner:
            stop.set()
            spinner_thread.join()

    elapsed = int(time.time() - start_time)
    if task.status == TaskStatus.DONE:
        summary = (task.result or {}).get("summary", "")[:150].replace("\n", " ")
        print(f"[{ts()}] ✓  [{agent_type.value}] done in {elapsed}s")
        print(f"           └─ {summary}")
    elif task.status == TaskStatus.FAILED:
        print(f"[{ts()}] ✗  [{agent_type.value}] failed after {elapsed}s")
    print()

    return task


# ─────────────────────────────────────────────
# BLACKBOX PIPELINE (unchanged behaviour)
# ─────────────────────────────────────────────

def run_blackbox_pipeline(
    orc: Orchestrator,
    q: TaskQueue,
    target: str,
    notes: str,
    flag_format: str,
) -> str | None:
    already_ran = set()
    completed   = []
    unexpected  = []
    found_flag  = None

    # Phase 1: web_recon always first
    print(f"[{ts()}] Phase 1 — web_recon\n")
    recon_task = run_agent(orc, AgentType.WEB_RECON, target, flag_format, [])
    already_ran.add("web_recon")
    if recon_task.status == TaskStatus.DONE:
        completed.append({"agent": "web_recon", "summary": (recon_task.result or {}).get("summary", "")})

    # Phase 2: Supervisor loop — flag detection is the supervisor's responsibility
    iteration = 0
    retried: set[str] = set()
    while not found_flag and iteration < MAX_ITERATIONS:
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
            "retry":     decision.get("retry"),
            "reason":    decision.get("reason", ""),
            "stop":      decision.get("stop", False),
        })
        print(f"           next={decision.get('next')} retry={decision.get('retry')} | {decision.get('reason', '')}\n")

        if decision.get("flag"):
            found_flag = decision["flag"]
            q.emit("flag_found", {"agent": "supervisor", "flag": found_flag})
            break

        # Handle retry
        retry_agent_str = decision.get("retry")
        if retry_agent_str and retry_agent_str not in retried:
            retried.add(retry_agent_str)
            try:
                retry_agent = AgentType(retry_agent_str)
            except ValueError:
                print(f"[{ts()}] ✗  Unknown retry agent '{retry_agent_str}' — skipping retry")
            else:
                print(f"[{ts()}] ↺  retrying [{retry_agent_str}]\n")
                dep_ids = [t.id for t in orc.tasks.values() if t.status == TaskStatus.DONE]
                retry_context = f"RETRY: previous output was insufficient. {decision.get('reason', '')} Be more thorough."
                task = run_agent(orc, retry_agent, target, flag_format, dep_ids,
                                 context_override=retry_context)
                if task.status == TaskStatus.DONE:
                    summary = (task.result or {}).get("summary", "")
                    completed = [c for c in completed if c["agent"] != retry_agent_str]
                    completed.append({"agent": retry_agent_str, "summary": summary})
            continue

        if decision.get("stop") or not decision.get("next"):
            break

        next_agent_str = decision["next"]
        try:
            next_agent = AgentType(next_agent_str)
        except ValueError:
            print(f"[{ts()}] ✗  Unknown agent '{next_agent_str}' — stopping")
            break

        dep_ids = [t.id for t in orc.tasks.values() if t.status == TaskStatus.DONE]
        task = run_agent(orc, next_agent, target, flag_format, dep_ids,
                         context_override=decision.get("context_for_next"))
        already_ran.add(next_agent_str)

        if task.status == TaskStatus.DONE:
            summary = (task.result or {}).get("summary", "")
            completed.append({"agent": next_agent_str, "summary": summary})
            unexp = scan_unexpected(summary)
            if unexp:
                unexpected.append({"agent": next_agent_str, "finding": unexp["raw"]})
        elif task.status == TaskStatus.FAILED:
            completed.append({"agent": next_agent_str, "summary": "[FAILED — no findings]"})

    return found_flag


# ─────────────────────────────────────────────
# WHITEBOX PIPELINE
# ─────────────────────────────────────────────

def run_whitebox_pipeline(
    orc: Orchestrator,
    q: TaskQueue,
    target: str,
    local_target: str,
    source_code: str,
    flag_format: str,
    notes: str,
) -> str | None:
    already_ran = set()
    completed   = []   # [{"agent": ..., "summary": ...}]
    found_flag  = None

    wb_kwargs = dict(local_target=local_target, source_code=source_code)

    # Phase 1+2: code_reader and dep_checker in parallel (independent — no shared target)
    print(f"[{ts()}] Phase 1+2 — code_reader + dep_checker (parallel)\n")
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_name = {
            executor.submit(
                run_agent, orc, AgentType.CODE_READER, target, flag_format, [],
                local_target=local_target, source_code=source_code, show_spinner=False,
            ): "code_reader",
            executor.submit(
                run_agent, orc, AgentType.DEP_CHECKER, target, flag_format, [],
                local_target=local_target, source_code=source_code, show_spinner=False,
            ): "dep_checker",
        }
        results = {}
        pending = set(future_to_name)
        for future in as_completed(future_to_name):
            results[future_to_name[future]] = future.result()
            pending.discard(future)
            if pending:
                still = ", ".join(future_to_name[f] for f in pending)
                print(f"[{ts()}]    waiting for: {still} ...\n")

    already_ran.update({"code_reader", "dep_checker"})
    for agent_name, task_obj in [("code_reader", results["code_reader"]), ("dep_checker", results["dep_checker"])]:
        if task_obj.status == TaskStatus.DONE:
            completed.append({"agent": agent_name, "summary": (task_obj.result or {}).get("summary", "")})

    # Phase 3: vuln_reasoner (depends on both)
    print(f"[{ts()}] Phase 3 — vuln_reasoner\n")
    dep_ids = [t.id for t in orc.tasks.values() if t.status == TaskStatus.DONE]
    vr_task = run_agent(orc, AgentType.VULN_REASONER, target, flag_format, dep_ids, **wb_kwargs)
    already_ran.add("vuln_reasoner")
    if vr_task.status == TaskStatus.DONE:
        completed.append({"agent": "vuln_reasoner", "summary": (vr_task.result or {}).get("summary", "")})
    else:
        print(f"[{ts()}] ✗  vuln_reasoner failed — cannot continue whitebox pipeline\n")
        return None

    # Phase 4: Supervisor loop
    available_auditors = {a.value for a in WHITEBOX_AUDITORS}
    iteration = 0
    retried: set[str] = set()

    while not found_flag and iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"[{ts()}] Supervisor — iteration {iteration}")

        decision = decide(
            target=target,
            flag_format=flag_format,
            completed=completed,
            unexpected=[],
            already_ran=already_ran,
            mode="whitebox",
        )

        q.emit("supervisor_decision", {
            "iteration": iteration,
            "next":      decision.get("next"),
            "retry":     decision.get("retry"),
            "reason":    decision.get("reason", ""),
            "stop":      decision.get("stop", False),
        })
        print(f"           next={decision.get('next')} retry={decision.get('retry')} | {decision.get('reason', '')}\n")

        if decision.get("flag"):
            found_flag = decision["flag"]
            q.emit("flag_found", {"agent": "supervisor", "flag": found_flag})
            break

        # Handle retry
        retry_agent_str = decision.get("retry")
        if retry_agent_str and retry_agent_str not in retried:
            retried.add(retry_agent_str)
            if retry_agent_str not in available_auditors:
                print(f"[{ts()}] ✗  retry target '{retry_agent_str}' is not a whitebox auditor — skipping")
            else:
                try:
                    retry_agent = AgentType(retry_agent_str)
                except ValueError:
                    print(f"[{ts()}] ✗  Unknown retry agent '{retry_agent_str}' — skipping")
                else:
                    print(f"[{ts()}] ↺  retrying [{retry_agent_str}]\n")
                    dep_ids = [t.id for t in orc.tasks.values() if t.status == TaskStatus.DONE]
                    retry_context = f"RETRY: previous output was insufficient. {decision.get('reason', '')} Be more thorough."
                    task = run_agent(orc, retry_agent, target, flag_format, dep_ids,
                                     context_override=retry_context, **wb_kwargs)
                    if task.status == TaskStatus.DONE:
                        summary = (task.result or {}).get("summary", "")
                        completed = [c for c in completed if c["agent"] != retry_agent_str]
                        completed.append({"agent": retry_agent_str, "summary": summary})
            continue

        if decision.get("stop") or not decision.get("next"):
            break

        next_agent_str = decision["next"]
        if next_agent_str not in available_auditors:
            print(f"[{ts()}] ✗  '{next_agent_str}' is not a whitebox auditor — stopping")
            break

        try:
            next_agent = AgentType(next_agent_str)
        except ValueError:
            print(f"[{ts()}] ✗  Unknown agent '{next_agent_str}' — stopping")
            break

        dep_ids = [t.id for t in orc.tasks.values() if t.status == TaskStatus.DONE]
        task = run_agent(orc, next_agent, target, flag_format, dep_ids,
                         context_override=decision.get("context_for_next"), **wb_kwargs)
        already_ran.add(next_agent_str)

        if task.status == TaskStatus.DONE:
            completed.append({"agent": next_agent_str, "summary": (task.result or {}).get("summary", "")})
        elif task.status == TaskStatus.FAILED:
            completed.append({"agent": next_agent_str, "summary": "[FAILED — no findings]"})

    return found_flag


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def cleanup_tmp(redis_client=None) -> None:
    """Wipe /tmp/aurelinth/, stray agent artifacts, and Redis state before a new run."""
    import glob

    # Flush Redis pipeline state — stale task IDs and events from previous runs
    if redis_client is not None:
        for key in redis_client.keys("aurelinth:*"):
            redis_client.delete(key)

    # Wipe dedicated agent directory
    aurelinth_tmp = "/tmp/aurelinth"
    if os.path.isdir(aurelinth_tmp):
        shutil.rmtree(aurelinth_tmp, ignore_errors=True)
    os.makedirs(aurelinth_tmp, exist_ok=True)

    # Wipe gemini-cli tool output cache — contains outputs from previous sessions
    # that agents will grep through if they search the filesystem for flag patterns
    gemini_cache = os.path.expanduser("~/.gemini/tmp")
    if os.path.isdir(gemini_cache):
        shutil.rmtree(gemini_cache, ignore_errors=True)

    # Remove stray files in /tmp/ root that agents may have written directly
    stray_patterns = [
        "/tmp/*.py",
        "/tmp/*.bak",
        "/tmp/*.pem",
        "/tmp/flag*",
        "/tmp/sqlmap_out",
        "/tmp/dalfox_out.txt",
    ]
    for pattern in stray_patterns:
        for path in glob.glob(pattern):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def run_pipeline(
    target: str,
    notes: str = "",
    flag_format: str = "",
    local_target: str = "",
    source_code: str = "",
) -> None:
    if not run_health_check():
        print("Aborting — fix errors above before running.")
        return

    db  = get_mongo()
    r   = get_redis()
    cleanup_tmp(redis_client=r)
    q   = TaskQueue(r)
    orc = Orchestrator(q, db)

    is_whitebox = bool(source_code)
    mode = "WHITEBOX" if is_whitebox else "BLACKBOX"

    print(f"\n{'='*60}")
    print(f"  AURELINTH — {ts()} — {mode}")
    print(f"  Target      : {target}")
    if is_whitebox:
        print(f"  Local       : {local_target or 'not provided'}")
        print(f"  Source      : {source_code}")
    print(f"  Notes       : {notes or 'none'}")
    print(f"  Flag format : {flag_format or 'unknown'}")
    print(f"{'='*60}\n")

    total_start = time.time()

    if is_whitebox:
        found_flag = run_whitebox_pipeline(
            orc, q, target, local_target, source_code, flag_format, notes
        )
    else:
        found_flag = run_blackbox_pipeline(
            orc, q, target, notes, flag_format
        )

    # Final report
    total  = int(time.time() - total_start)
    done   = [t for t in orc.tasks.values() if t.status == TaskStatus.DONE]
    failed = [t for t in orc.tasks.values() if t.status == TaskStatus.FAILED]

    print(f"{'='*60}")
    print(f"  COMPLETE — {ts()} — total {total}s")
    print(f"  Mode       : {mode}")
    print(f"  Agents run : {len(orc.tasks)}")
    print(f"  Done/Failed: {len(done)}/{len(failed)}")
    if found_flag:
        print(f"\n{'🚩'*30}")
        print(f"  FLAG CAPTURED")
        print(f"  {found_flag}")
        print(f"  Target  : {target}")
        print(f"  Time    : {total}s")
        print(f"{'🚩'*30}\n")
    print(f"{'='*60}\n")

    q.emit("pipeline_complete", {
        "target":     target,
        "mode":       mode.lower(),
        "flag":       found_flag or None,
        "total_time": total,
        "agents_run": len(orc.tasks),
        "done":       len(done),
        "failed":     len(failed),
    })

    for task in orc.tasks.values():
        if task.agent_type == AgentType.FLAG_EXTRACTOR and task.result:
            print("FINAL REPORT:")
            print("─"*60)
            print(task.result.get("summary", "No output"))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Aurelinth — CTF Web Agent")
    parser.add_argument("target",                        nargs="?", help="Real target URL")
    parser.add_argument("--notes",        default="",   help="Challenge notes")
    parser.add_argument("--flag-format",  default="",   help="e.g. picoCTF{...}")
    parser.add_argument("--local-target", default="",   help="Local target URL (whitebox)")
    parser.add_argument("--source-code",  default="",   help="Path to source code (whitebox)")
    parser.add_argument("--health-check", action="store_true", help="Run health check and exit")
    args = parser.parse_args()

    if args.health_check:
        import sys
        ok = run_health_check(verbose=True)
        sys.exit(0 if ok else 1)

    if not args.target:
        parser.error("target is required unless --health-check is used")

    run_pipeline(
        target       = args.target,
        notes        = args.notes,
        flag_format  = args.flag_format,
        local_target = args.local_target,
        source_code  = args.source_code,
    )