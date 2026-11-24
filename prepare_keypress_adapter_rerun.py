"""Freeze all tasks stopped by the previous Android key adapter."""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import watch_unipath_resume as watcher

ROOT = Path(r"H:\GUI_AGENT_runs\ui_path_screen_agent\kg_rag_v2_hard_intents")
SOURCE_ROOTS = [
    ROOT / "gpt56sol_medium",
    ROOT / "gpt56sol_medium_gate_rerun",
    ROOT / "gpt56sol_medium_keypress_rerun",
]
OUTPUT_ROOT = ROOT / "gpt56sol_medium_android_key_adapter_rerun_20261025"
DEST = Path(__file__).with_name("keypress_adapter_rerun_20261025.json")
ALREADY_RERUN_ROOT = ROOT / "gpt56sol_medium_keypress_rerun"


def main():
    reasons = defaultdict(list)
    for source_root in SOURCE_ROOTS:
        for result_path in source_root.rglob("task_result.json"):
            try:
                result = json.loads(result_path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            reason = str(result.get("reason", ""))
            if reason.startswith(("unsupported_key:", "unsupported_keycombination:", "invalid_keypress:")):
                key = f"{result.get('package')}/{result.get('test_id')}"
                reasons[key].append({"reason": reason, "source_result": str(result_path)})

    # Exclude the earlier 13-task keypress rerun when it reached a terminal
    # runner result; those tasks no longer need another adapter attempt.
    already_terminal = set()
    for result_path in ALREADY_RERUN_ROOT.rglob("task_result.json"):
        try:
            result = json.loads(result_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        if result.get("status") in {"completed", "max_steps", "human_confirmation"}:
            already_terminal.add(f"{result.get('package')}/{result.get('test_id')}")

    configured = {f"{task['package']}/{task['test_id']}": task for task in watcher.task_list()}
    reasons = {key: value for key, value in reasons.items() if key not in already_terminal}
    selected = sorted(set(reasons) & set(configured))
    missing = sorted(set(reasons) - set(configured))
    if missing:
        raise RuntimeError(f"Affected tasks missing from current dataset config: {missing}")
    payload = {
        "created_at": datetime.now().isoformat(),
        "reason": "previous Android key adapter stopped on unsupported key input",
        "selected": selected,
        "source_failures": dict(reasons),
        "output_root": str(OUTPUT_ROOT),
        "allow_external_side_effects": False,
        "rerun_command": "watch_unipath_resume.py --until <LOCAL_ISO_TIME> --rerun-selection " + str(DEST),
    }
    DEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"count": len(selected), "destination": str(DEST), "output_root": str(OUTPUT_ROOT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
