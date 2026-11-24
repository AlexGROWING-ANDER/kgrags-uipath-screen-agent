# KG-RAG × UiPath Screen Agent mobile adapter

This adapter preserves the public UiPath planner and grounder and adds only:

- Android screenshot and action execution through ADB;
- KG-RAG intent loading;
- isolated trajectory/result persistence;
- a default stop before external side effects.

Each model round captures one `step_NN.png` before prediction. That frame is
the model input for that round and can show the result of the preceding action.
There is no second capture after actions, including on the terminal step.
`trajectory.jsonl`, `action_execution.jsonl`, and `task_result.json` still
record predictions, execution, and the runner's terminal status, respectively.

The public sample data uses a placeholder email recipient. Configure a test
recipient in the local fixture before running the email case.

Preflight without model calls or phone actions:

```powershell
& 'H:/GUI_AGENT_OSWorld/venv-v1/Scripts/python.exe' -X utf8 `
  'C:/Users/ASUS/Documents/Codex/2026-09-19/new-chat/unipath_mobile/run_mobile_uipath.py' `
  --package com.baidu.baidutranslate `
  --intent-file 'E:/GUI_AGENT架构归因/hard_intents/com.baidu.baidutranslate.json' `
  --test-id test_1 `
  --preflight-only
```

Remove `--preflight-only` for the isolated smoke run. It writes only under:

`H:/GUI_AGENT_runs/ui_path_screen_agent/kg_rag_v2_hard_intents/gpt56sol_medium/<timestamp>/`


The public fixtures use sample contact and address values. Configure local test values before running mail and address cases. Device checks and run audits are stored with the experiment results.
