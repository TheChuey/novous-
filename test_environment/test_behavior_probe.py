import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_environment import behavior_probe, model_log


def make_chat(answers):
    def chat(**kwargs):
        question = kwargs["messages"][-1]["content"]
        for key, value in answers.items():
            if key in question:
                return {"message": {"content": value}}
        return {"message": {"content": ""}}
    return chat


GOOD = {
    "Who are you": "I am a Prompt Builder that writes prompts for agents.",
    "Summarize": "I help users write clear prompts for agents.",
    "capital of France": "The capital of France is Paris.",
    "Zorblax": "I'm not aware of any such keynote; I can't verify it.",
}


class BehaviorProbeTests(unittest.TestCase):
    def run_probes(self, answers):
        return behavior_probe.run_probes(
            "m1", "You are a Prompt Builder.", "Prompt Builder", "Help users write clear prompts for agents.",
            chat=make_chat(answers))

    def test_good_model_passes_everything(self):
        result = self.run_probes(GOOD)
        self.assertTrue(all(c["passed"] for c in result["components"]))
        self.assertEqual(result["weaknesses"], [])
        self.assertEqual(len(result["strengths"]), 4)

    def test_hallucination_and_fact_failures_give_improvements(self):
        bad = dict(GOOD)
        bad["Zorblax"] = "He said agriculture on the Moon will feed billions by 2050."
        bad["capital of France"] = "Lyon."
        result = self.run_probes(bad)
        failed = {c["checks"][0]["id"] for c in result["components"] if not c["passed"]}
        self.assertEqual(failed, {"fact_correct", "no_invention"})
        self.assertEqual(len(result["improvements"]), 2)
        self.assertIn("Never invent", " ".join(result["improvements"]))

    def test_role_failure_when_title_not_reflected(self):
        bad = dict(GOOD)
        bad["Who are you"] = "I am a large language model."
        result = self.run_probes(bad)
        self.assertFalse(result["components"][0]["passed"])

    def test_custom_fact_question(self):
        result = behavior_probe.run_probes(
            "m1", "p", "Prompt Builder", "Help users", "What is 2+2?", "4",
            chat=make_chat({**GOOD, "2+2": "It is 4."}))
        self.assertTrue(result["components"][2]["passed"])


class ModelLogTests(unittest.TestCase):
    def test_one_file_per_model_with_cap(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(model_log, "LOG_DIR", Path(tmp)):
            comp = [{"checks": [{"id": "fact_correct", "passed": False}]}]
            for _ in range(model_log.MAX_ENTRIES + 3):
                log = model_log.record_run("qwen2.5-coder:latest", "T", False, comp, [], ["w"], ["i"])
            model_log.record_run("other", "T", True, [], [], [], [])
            files = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(files, ["other.json", "qwen2.5-coder-latest.json"])
            self.assertEqual(log["runs"], model_log.MAX_ENTRIES + 3)
            self.assertEqual(len(model_log.get_log("qwen2.5-coder:latest")["entries"]), model_log.MAX_ENTRIES)
            self.assertEqual(log["probe_failures"], {"fact_correct": model_log.MAX_ENTRIES + 3})


if __name__ == "__main__":
    unittest.main()
