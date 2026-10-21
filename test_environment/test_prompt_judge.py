import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_environment import prompt_judge, report_store


class PromptJudgeTests(unittest.TestCase):
    def fake_chat(self, **kwargs):
        self.requested_model = kwargs["model"]
        return {"message": {"content": (
            'Here you go:\n[{"id":"prompt","passed":true,"reason":"consistent","fix":""},'
            '{"id":"section-0","passed":false,"reason":"too vague","fix":"Name the domain."}]'
        )}}

    def test_judge_maps_verdicts_to_components(self):
        result = prompt_judge.judge_prompt(
            "m1", "T", "D", [{"title": "Role", "content": "You are helpful."}], [], chat=self.fake_chat)
        self.assertEqual(self.requested_model, "m1")
        self.assertEqual(result["model"], "m1")
        by_name = {c["name"]: c for c in result["components"]}
        self.assertTrue(by_name["AI review: Whole prompt"]["passed"])
        failed = by_name["AI review: Role"]
        self.assertFalse(failed["passed"])
        self.assertEqual(failed["checks"][0]["fix"], "Name the domain.")

    def test_judge_rejects_non_json(self):
        with self.assertRaises(ValueError):
            prompt_judge.judge_prompt("m", "T", "D", [], [], chat=lambda **k: {"message": {"content": "nope"}})


class ReportStoreTests(unittest.TestCase):
    def test_save_list_get_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(report_store, "REPORTS_DIR", Path(tmp)):
            record = report_store.save_report("prompt", "My Prompt", "m1", {"passed": False, "verdict": "FAIL"}, notes="n")
            listed = report_store.list_reports()
            self.assertEqual([r["id"] for r in listed], [record["id"]])
            self.assertEqual(listed[0]["model"], "m1")
            self.assertEqual(report_store.get_report(record["id"])["notes"], "n")
            with self.assertRaises(ValueError):
                report_store.get_report("../x")


if __name__ == "__main__":
    unittest.main()
