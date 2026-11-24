"""Freeze the priority queue without launching or changing annotations."""
import json
from pathlib import Path

ROOT=Path(__file__).parent
old=json.loads((ROOT/'confirmation_repair_20261026/rerun_selection.json').read_text(encoding='utf-8'))
workspace=ROOT.parent
cases=json.loads((workspace/'attribution_viewer/unipath_review_20261024/snapshot.json').read_text(encoding='utf-8'))['cases']
selected_cases=[c for c in cases if f"{c['package']}/{c['test_id']}" in old['selected']]
assert len(selected_cases)==15
review_key='me.ele/test_4'
selected=[f"{c['package']}/{c['test_id']}" for c in selected_cases if f"{c['package']}/{c['test_id']}"!=review_key]
# Live streams may leave floating players: schedule those tasks last.
selected.sort(key=lambda k:(k.startswith(('air.tv.douyu.android/','com.duowan.kiwi/')),old['selected'].index(k)))
out=ROOT/'confirmation_priority_20261027'
out.mkdir(exist_ok=True)
manifest={**old,'created_at':'2026-10-27','adapter_version':'android-input-verified-v4-20261026',
 'selected':selected,'priority':'UniPath confirmation repair before Agent-S2 reruns',
 'requires_initial_state_review':True,'initial_state_ready':[],
 'allow_external_side_effects':True,'allow_email_tasks':True,
 'review_before_rerun':[review_key],
 'preflight_notes':{'com.baidu.BaiduMap/test_3':'Instruction says Gaode but package is Baidu; resolve before marking ready.',
                    'air.tv.douyu.android/test_2':'Run last; dismiss floating live player before ending.'},
 'output_root':'H:/GUI_AGENT_runs/ui_path_screen_agent/kg_rag_v2_hard_intents/gpt56sol_medium_confirmation_priority_20261027'}
(out/'rerun_selection.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
bykey={f"{c['package']}/{c['test_id']}":c for c in selected_cases}
lines=['# UniPath人工确认误拦：优先补跑队列（2026-10-27）','',
 '优先于Agent-S2新增补跑。14条补跑候选，另1条先核实际完成证据。清单已准备，未启动任务、未修改网站标注。',
 '执行前须人工恢复各任务初始状态并逐条验收，不能批量将initial_state_ready写满。保留登录和任务必要的历史数据，不清空全部收藏/联系人/购物车。',
 '新版已实测文字输入和组合键，但完整业务任务仍需重跑验证。启动时同时显式传递--allow-external-side-effects及--allow-email-tasks，避免重新落回旧授权设置。','',
 '| 网站序号 | 任务 | 处理 |','|---|---|---|']
for key in selected:
 c=bykey[key]
 note='先恢复初态，再补跑'
 if key=='com.baidu.BaiduMap/test_3':note='先确认高德指令与百度包名冲突'
 if key.startswith('air.tv.douyu.android/'):note='直播类最后跑，结束时处理悬浮播放器'
 lines.append(f"| {c['number']} | **{c['package']} - {c['intent']}** (`{c['test_id']}`) | {note} |")
lines+=['','## 先核实，不直接重复写操作','',
 '**第70条 · me.ele / test_4**：进入水果店，添加前三个商品到购物车，再删掉其中一个。旧门控拦的是finish摘要，可能已经有完整成功证据。先核对实际增删及剩余商品；只有不满足时才恢复初态补跑。','',
 '第66条邮件任务需要检查是否已存在指定联系人及是否已发送对应邮件，避免重建或重复发出；旧任务授权仍有效，但不能用旧完成状态充当本轮动作。']
(out/'优先补跑清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'selected':len(selected),'review_only':1,'ready':0,'started':False,'manifest':str(out/'rerun_selection.json')},ensure_ascii=False))
