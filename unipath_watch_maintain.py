"""Quiet UniPath watch recovery with a selection queue.

Runs one watch at a time. When the active selection has produced a terminal
result for every selected task, the next selection in QUEUE starts
automatically. Never duplicates a live watch and never clears phone state.
"""
import datetime as dt
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
PRIORITY = HERE / "confirmation_priority_20261027"
PY = Path("H:/GUI_AGENT_OSWorld/venv-v1/Scripts/pythonw.exe")
WATCH = HERE / "watch_unipath_resume.py"
STOP = HERE / "UNIPATH_STOP"
DEADLINE = "2026-10-27T18:00:00"
LOG = HERE / "unipath_maintain.log"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Order matters: the confirmation/input-fix batch first, then the
# state-pollution reruns whose initial states were already restored.
QUEUE = [
    PRIORITY / "rerun_selection_inputfix_20261027.json",
    PRIORITY / "rerun_selection_statefix_20261027.json",
]


def watch_alive() -> bool:
    command = (
        "@(Get-CimInstance Win32_Process | Where-Object {"
        "$_.Name -match '^pythonw?\\.exe$' -and $_.CommandLine -match 'watch_unipath_resume'"
        "}).Count"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW,
        )
        if result.returncode:
            return True  # discovery failed -> assume alive, never race
        return int((result.stdout or "0").strip() or 0) > 0
    except Exception:
        return True


def selection_state(selection_path: Path) -> tuple[bool, str]:
    """Return (is_complete, reason). Complete means every selected task has a result."""
    try:
        selection = json.loads(selection_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, f"unreadable:{exc}"
    selected = selection.get("selected") or []
    if not selected:
        return True, "empty"
    root = Path(selection.get("output_root", ""))
    if not root.is_dir():
        return False, "no-output-yet"
    missing = []
    for key in selected:
        package, _, test_id = key.partition("/")
        if not list(root.glob(f"*/{package}/{test_id}/task_result.json")):
            missing.append(key)
    if missing:
        return False, f"pending:{len(missing)}"
    return True, "complete"


def spawn(selection_path: Path) -> None:
    args = [
        str(PY), "-u", "-X", "utf8", str(WATCH),
        "--until", DEADLINE,
        "--rerun-selection", str(selection_path),
        "--allow-external-side-effects", "--allow-email-tasks",
    ]
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"\n[{dt.datetime.now().isoformat()}] spawn watch: {selection_path.name}\n")
        handle.flush()
        subprocess.Popen(args, cwd=str(WORK), stdout=handle, stderr=handle,
                         creationflags=NO_WINDOW)


def output_root(selection_path: Path) -> Path:
    try:
        return Path(json.loads(selection_path.read_text(encoding="utf-8-sig")).get("output_root", ""))
    except Exception:
        return Path("")


def stuck_watch_pid() -> int | None:
    """PID of a live watch waiting for a task that is no longer queued.

    The current batch was launched before one of its tasks was withdrawn. The
    running watch still holds the old task list, so it blocks forever on that
    key. Only that specific process is retired; a healthy watch on the next
    batch must keep running.
    """
    ready: set[str] = set()
    for selection_path in QUEUE:
        try:
            ready.update(json.loads(selection_path.read_text(encoding="utf-8-sig"))
                         .get("initial_state_ready") or [])
        except Exception:
            continue
    for selection_path in QUEUE:
        watch_root = output_root(selection_path) / "watch"
        if not watch_root.is_dir():
            continue
        candidates = sorted(watch_root.glob("*/status.json"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            continue
        newest = candidates[-1]
        # Only a live watch refreshes its heartbeat; ignore stale runs.
        if dt.datetime.now().timestamp() - newest.stat().st_mtime > 180:
            continue
        try:
            state = json.loads(newest.read_text(encoding="utf-8"))
        except Exception:
            continue
        if state.get("status") != "waiting_for_initial_state":
            continue
        task = state.get("task")
        pid = state.get("pid")
        if task and task not in ready and isinstance(pid, int):
            return pid
    return None


def retire_pid(pid: int) -> None:
    try:
        subprocess.run(["taskkill.exe", "/PID", str(pid), "/T", "/F"],
                       capture_output=True, timeout=30, creationflags=NO_WINDOW)
    except Exception:
        pass


def main() -> None:
    if STOP.exists():
        return
    if dt.datetime.now() >= dt.datetime.fromisoformat(DEADLINE):
        return
    if watch_alive():
        stalled = stuck_watch_pid()
        if stalled:
            with LOG.open("a", encoding="utf-8") as handle:
                handle.write(f"[{dt.datetime.now().isoformat()}] retire stalled watch pid={stalled}\n")
            retire_pid(stalled)
        return
    for selection_path in QUEUE:
        if not selection_path.exists():
            continue
        complete, reason = selection_state(selection_path)
        if complete:
            continue
        with LOG.open("a", encoding="utf-8") as handle:
            handle.write(f"[{dt.datetime.now().isoformat()}] {selection_path.name} -> {reason}\n")
        spawn(selection_path)
        return


if __name__ == "__main__":
    main()
