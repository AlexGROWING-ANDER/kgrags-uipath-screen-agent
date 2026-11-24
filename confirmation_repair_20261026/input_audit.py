"""Flag text-input failures from the current frozen website, without reruns."""
import json,re
from collections import Counter
from pathlib import Path

P=Path(__file__).resolve().parent
ROOT=P.parents[1]
data=json.loads((ROOT/'attribution_viewer/unipath_review_20261024/snapshot.json').read_text(encoding='utf-8'))
failure=re.compile(r'未(?:能|成功|实际|正确)?(?:输入|写入|出现|显示|生效|改变)|输入.{0,18}(?:失败|无效|未生效)|仍(?:然)?(?:显示|是|为|保留)|没有.{0,12}(?:输入|文字|文本|变化)|未发生变化|not (?:enter|appear|change)|unchanged',re.I)
rows=[]
for c in data['cases']:
 entries=[];steps=c['steps']
 for index,s in enumerate(steps):
  resp=s.get('response',{});a=[a for a in resp.get('actions',[]) if a.get('method_type')=='type_into']
  if not a:continue
  nextresp=steps[index+1].get('response',{}) if index+1<len(steps) else {}
  review=(nextresp.get('additional_parameters') or {}).get('review','')
  entries.append({'step':s['step'],'lengths':[len(str(x.get('parameters',{}).get('value',''))) for x in a],
                  'next_review':review,'failure_text_candidate':bool(failure.search(review))})
 if entries:rows.append({'number':c['number'],'package':c['package'],'test_id':c['test_id'],'intent':c['intent'],
                        'source':c['source'],'status':c['result']['status'],'adapter_version':c['result'].get('adapter_version'),
                        'type_into_calls':len(entries),'failure_candidates':sum(e['failure_text_candidate'] for e in entries),
                        'entries':entries})
(P/'input_audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
summary={'tasks_with_type_into':len(rows),'type_into_steps':sum(c['type_into_calls'] for c in rows),
         'tasks_with_failure_text_candidates':sum(c['failure_candidates']>0 for c in rows),
         'failure_review_candidates':sum(c['failure_candidates'] for c in rows),
         'new_adapter_website_results':sum(bool(c['adapter_version']) for c in rows),
         'status_counts':dict(Counter(c['status'] for c in rows))}
(P/'input_audit_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
for c in rows:
 if c['number'] in [3,4,10,25,66,83,105]:
  print(c['number'],c['package'],c['test_id'],c['type_into_calls'],c['failure_candidates'])
  for e in c['entries'][:3]:print(e['step'],e['next_review'][:210])
