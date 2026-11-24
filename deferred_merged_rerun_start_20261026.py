"""Start the merged UniPath rerun queue after the active queue exits."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
PYTHONW = Path("H:/GUI_AGENT_OSWorld/venv-v1/Scripts/pythonw.exe")
WATCHER = WORK / "unipath_mobile" / "watch_unipath_resume.py"
LOG = WORK / "unipath_mobile" / "deferred_merged_rerun_20261026.log"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-pid", type=int, required=True)
    parser.add_argument("--wait-status", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    return parser.parse_args()


def process_alive(pid: int) -> bool:
    result = subprocess.run(
        ["tasklist.exe", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.returncode == 0 and f'"{pid}"' in result.stdout


def recorded_complete(status_path: Path) -> bool:
    try:
        data = json.loads(status_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return False
    return data.get("status") == "complete"


def main() -> int:
    args = parse_args()
    deadline = dt.datetime.now() + dt.timedelta(days=3)
    while dt.datetime.now() < deadline:
        if recorded_complete(args.wait_status) or not process_alive(args.wait_pid):
            break
        time.sleep(30)
    else:
        return 2

    until = (dt.datetime.now() + dt.timedelta(days=2)).isoformat(timespec="seconds")
    command = [
        str(PYTHONW), "-u", str(WATCHER),
        "--until", until,
        "--rerun-selection", str(args.selection),
        "--allow-external-side-effects",
        "--allow-email-tasks",
        "--max-attempts", "2",
        "--task-timeout-seconds", "2700",
    ]
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"{dt.datetime.now().isoformat()} starting merged rerun until={until}\n")
        child = subprocess.Popen(
            command,
            cwd=WORK,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        log.write(f"pid={child.pid}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
