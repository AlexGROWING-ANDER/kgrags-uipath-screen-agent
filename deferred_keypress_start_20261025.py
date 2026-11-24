"""After the current phone task reaches a terminal result, switch to UniPath key-adapter reruns."""
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

WORK = Path(__file__).resolve().parents[1]
PHONE_ROOT = Path('H:/GUI_AGENT_runs/mobile_agent_v3/abnormal_rerun_20261025')
PHONE_MANIFEST = WORK / 'mail_publish_recovery_20261024' / 'manifest.json'
PAUSE = WORK / 'mail_publish_recovery_20261024' / 'PAUSE_AFTER_CURRENT'
SELECTION = WORK / 'unipath_mobile' / 'keypress_adapter_rerun_20261025.json'
PY = Path('H:/GUI_AGENT_OSWorld/venv-v1/Scripts/pythonw.exe')
WATCHER = WORK / 'unipath_mobile' / 'watch_unipath_resume.py'
LOG = WORK / 'unipath_mobile' / 'deferred_keypress_start_20261025.log'
LOCK = WORK / 'unipath_mobile' / 'deferred_keypress_start_20261025.lock'

def qqmusic_terminal():
    for p in PHONE_ROOT.glob('batch_*/summary.json'):
        try:
            d=json.loads(p.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):
            continue
        for row in d.get('results',[]):
            if row.get('app_package')=='com.tencent.qqmusic' and row.get('test_id')=='test_5':
                return row.get('status') in {'success','error','step_limit','human_confirmation'}
    return False

def main():
    try:
        handle=LOCK.open('x', encoding='utf-8')
        handle.write(dt.datetime.now().astimezone().isoformat())
        handle.close()
    except FileExistsError:
        return
    deadline=dt.datetime.now()+dt.timedelta(hours=12)
    try:
        while dt.datetime.now()<deadline:
            if qqmusic_terminal():
                PAUSE.write_text(dt.datetime.now().astimezone().isoformat(),encoding='utf-8')
                until=(dt.datetime.now()+dt.timedelta(hours=10)).isoformat(timespec='seconds')
                with LOG.open('a',encoding='utf-8') as log:
                    log.write(f'switching_after_qqmusic until={until}\n')
                    child=subprocess.Popen([str(PY),'-u',str(WATCHER),'--until',until,'--rerun-selection',str(SELECTION)],cwd=WORK,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
                    log.write(f'unipath_pid={child.pid}\n')
                return
            time.sleep(15)
    finally:
        LOCK.unlink(missing_ok=True)

if __name__=='__main__':main()
