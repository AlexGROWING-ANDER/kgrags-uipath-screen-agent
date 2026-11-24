import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent))
import run_mobile_uipath as adapter


class Completed:
    returncode = 0
    stdout = "input commands: keyevent keycombination"
    stderr = ""


class AndroidAdapterTests(unittest.TestCase):
    def test_accepts_string_and_list_key_payloads(self):
        with patch.object(adapter, "adb_run", return_value=Completed()) as adb_run:
            self.assertEqual(adapter.execute_keypress(Path("adb"), "Ctrl+A"), (False, "executed"))
            self.assertEqual(adapter.execute_keypress(Path("adb"), ["PgDn"]), (False, "executed"))
        self.assertEqual(adb_run.call_count, 3)

    def test_unsupported_keys_are_not_confirmation_requests(self):
        self.assertEqual(adapter.result_status("unsupported_key:ctrl"), "unsupported_action")
        self.assertEqual(adapter.result_status("unsupported_keycombination:device_input_command"), "unsupported_action")
        self.assertEqual(adapter.result_status("human_confirmation_required:send message"), "human_confirmation")
        self.assertEqual(adapter.result_status("finished"), "completed")


class AndroidScreenshotTests(unittest.IsolatedAsyncioTestCase):
    async def test_only_model_observations_are_saved(self):
        for finish, expected_status in ((True, "completed"), (False, "max_steps")):
            with self.subTest(finish=finish), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fake_agent = ModuleType("mm_agents.uipath.agent")
                predict = AsyncMock(side_effect=[
                    {"step": {"actions": [{"method_type": "click"}]}},
                    {"step": {"actions": [{"method_type": "finish" if finish else "click"}]}},
                ])
                fake_agent.UiPathComputerUseV1 = lambda: SimpleNamespace(predict_request=predict)
                args = SimpleNamespace(
                    adb=Path(__file__), output_root=root, package="test.app", test_id="test_1",
                    intent_file=None, max_steps=2, runtime_only=False, preflight_only=False,
                    allow_external_side_effects=False,
                )

                def fake_screenshot(_adb: Path, path: Path) -> bytes:
                    frame = path.name.encode("ascii")
                    path.write_bytes(frame)
                    return frame

                with (
                    patch.dict(sys.modules, {fake_agent.__name__: fake_agent}),
                    patch.dict(adapter.os.environ), patch.object(sys, "path", sys.path.copy()),
                    patch.object(adapter, "UIPATH_REPO", root),
                    patch.object(adapter, "load_intent", return_value="Test intent"),
                    patch.object(adapter.communication_permissions, "set_task_intent"),
                    patch.object(adapter, "dotenv_values", return_value={
                        "MOBILE_AGENT_BASE_URL": "https://example.invalid",
                        "MOBILE_AGENT_API_KEY": "unused-test-value",
                    }),
                    patch.object(adapter, "adb_device", return_value="fake-device"),
                    patch.object(adapter, "adb_run", return_value=SimpleNamespace(stdout="package:test.app")),
                    patch.object(adapter.time, "sleep"),
                    patch.object(adapter, "screenshot", side_effect=fake_screenshot) as capture,
                    patch.object(adapter, "execute_action", side_effect=[
                        (False, "executed"), (True, "finished") if finish else (False, "executed"),
                    ]),
                ):
                    self.assertEqual(await adapter.run(args), 0 if finish else 2)

                out = next(root.glob("*/test.app/test_1"))
                observed = ["step_01.png", "step_02.png"]
                self.assertEqual([call.args[1].name for call in capture.call_args_list], observed)
                self.assertEqual(sorted(path.name for path in out.glob("*.png")), observed)
                self.assertEqual([base64.b64decode(call.args[0]["image"]).decode("ascii")
                                  for call in predict.await_args_list], observed)
                result = json.loads((out / "task_result.json").read_text(encoding="utf-8"))
                self.assertEqual((result["status"], result["steps"]), (expected_status, 2))
                for filename in ("trajectory.jsonl", "action_execution.jsonl"):
                    with (out / filename).open(encoding="utf-8") as log:
                        self.assertEqual([json.loads(line)["step"] for line in log], [1, 2])


if __name__ == "__main__":
    unittest.main()
