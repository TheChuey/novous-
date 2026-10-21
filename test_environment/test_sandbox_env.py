import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_environment import sandbox_env


class SandboxEnvTests(unittest.TestCase):
    def test_package_names_are_validated(self):
        self.assertEqual(sandbox_env.validate_packages(["streamlit", "requests==2.31.0", "numpy>=1.0"]),
                         ["streamlit", "requests==2.31.0", "numpy>=1.0"])
        for bad in ["--index-url http://x", "git+https://x/y", "../local", "a b", "", "pkg;rm"]:
            with self.assertRaises(ValueError, msg=bad):
                sandbox_env.validate_packages([bad])

    def test_third_party_modules_skip_stdlib_and_project_modules(self):
        source = "import os, json\nimport streamlit as st\nfrom cv2 import imread\nfrom tools import interface\nimport a.b\n"
        self.assertEqual(sandbox_env.third_party_modules(source), ["streamlit", "cv2", "a"])
        self.assertEqual(sandbox_env.package_for_module("cv2"), "opencv-python")

    def test_install_uses_sandbox_pip_with_validated_names(self):
        with patch.object(sandbox_env, "ensure_venv", return_value={"ok": True, "output": ""}), \
                patch.object(sandbox_env, "_run", return_value={"ok": True, "output": "done"}) as run:
            result = sandbox_env.install(["streamlit"])
        self.assertTrue(result["ok"])
        command = run.call_args[0][0]
        self.assertEqual(command[1:4], ["-m", "pip", "install"])
        self.assertEqual(command[-1], "streamlit")

    def test_promotion_appends_only_new_packages_to_requirements(self):
        with tempfile.TemporaryDirectory() as temp:
            requirements = Path(temp) / "requirements.txt"
            requirements.write_text("fastapi>=0.110.0\nrequests>=2.0", encoding="utf-8")
            source = "import fastapi\nimport requests\nimport streamlit\nimport cv2\n"
            with patch.object(sandbox_env, "REQUIREMENTS_PATH", requirements), \
                    patch.object(sandbox_env, "list_packages",
                                 return_value=[{"name": "streamlit", "version": "1.40.0"}]):
                added = sandbox_env.add_to_requirements(source)
                again = sandbox_env.add_to_requirements(source)
            self.assertEqual(added, ["streamlit>=1.40.0", "opencv-python"])
            self.assertEqual(again, [])
            lines = requirements.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines, ["fastapi>=0.110.0", "requests>=2.0", "streamlit>=1.40.0", "opencv-python"])


if __name__ == "__main__":
    unittest.main()
