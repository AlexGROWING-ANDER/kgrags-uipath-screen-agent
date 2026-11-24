"""Read-only replay of website stops; prepare a separate, manual-reset queue."""
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P.parent))
import run_mobile_uipath as adapter

def main():
    snapshot=adapter.WORKSPACE/'attribution_viewer/unipath_review_20261024/snapshot.json'
    rows=json.loads(snapshot.read_text(encoding='utf-8'))['cases']
    stopped=[]
    for c in rows:
        if c['result'].get('status')!='human_confirmation':continue
        src=Path(c['source']);last=json.loads((src/'trajectory.jsonl').read_text(encoding='utf-8').splitlines()[-1])
        step=last['response'];actions=adapter.execution_actions(step)
        stopped.append({'number':c['number'],'package':c['package'],'test_id':c['test_id'],
            'intent':c['intent'],'source':str(src),'step':last['step'],'old_reason':c['result'].get('reason'),
            'original_actions':step.get('actions'), 'corrected_actions':actions,
            'confirmation_with_authorization':any(adapter.requires_confirmation(a,True,True) for a in actions),
            'confirmation_without_authorization':any(adapter.requires_confirmation(a,False,False) for a in actions)})
    assert all(not c['confirmation_with_authorization'] for c in stopped)
    (P/'replay_audit.json').write_text(json.dumps(stopped,ensure_ascii=False,indent=2),encoding='utf-8')
    selection={'created_at':dt.datetime.now().isoformat(),'reason':'confirmation false positives and upstream Backspace/Delete conversion repair',
        'adapter_version':adapter.ADAPTER_VERSION,'selected':[f"{c['package']}/{c['test_id']}" for c in stopped],
        'allow_external_side_effects':True,'requires_initial_state_review':True,'initial_state_ready':[],
        'output_root':'H:/GUI_AGENT_runs/ui_path_screen_agent/kg_rag_v2_hard_intents/gpt56sol_medium_confirmation_repair_20261026',
        'source_results':{f"{c['package']}/{c['test_id']}":str(Path(c['source'])/'task_result.json') for c in stopped},
        'instructions':'Only add a task key to initial_state_ready after the required manual reset is checked. Do not bulk mark ready.'}
    (P/'rerun_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# UniPath人工确认误拦修复：待补跑清单','',
        '仅准备，尚未启动。每条须先人工确认初始状态，验收后才添加到rerun_selection.json的initial_state_ready。保留登录，不统一清空必要收藏、历史。',
        '', '| 网站序号 | 任务 | 原停止步骤 | 旧原因 |', '|---|---|---|---|']
    for c in stopped:lines.append(f"| {c['number']} | **{c['package']} / {c['test_id']}**：{c['intent']} | {c['step']} | {c['old_reason']} |")
    lines+=['','回放只检查旧停止动作经过修复后的门控和按键转换，未调用模型、未操作手机，不等于重跑任务成功。',
        '第70条旧记录是在finish摘要上误拦；它可能已有完整成功证据，可先人工核实，无需为了改终止标签就重复执行购物车写操作。旧结果不直接改写。']
    (P/'待补跑清单.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'website_cases':len(rows),'confirmation_stops':len(stopped),
        'methods':dict(Counter(a['method_type'] for c in stopped for a in c['corrected_actions'])),
        'still_gated_with_authorization':sum(c['confirmation_with_authorization'] for c in stopped),
        'still_gated_without_authorization':sum(c['confirmation_without_authorization'] for c in stopped)},ensure_ascii=False))
if __name__=='__main__':main()
