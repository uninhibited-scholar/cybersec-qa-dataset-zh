import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deploy_candidate.py"

class DeployCandidateTests(unittest.TestCase):
    def setup_case(self, eligible=True, passed=True):
        root = Path(tempfile.mkdtemp())
        candidate, production = root / "candidate", root / "production"
        candidate.mkdir(); production.mkdir()
        (candidate / "new.safetensors").write_text("new")
        (production / "stale.safetensors").write_text("stale")
        approval = root / "approval.json"; approval.write_text(json.dumps({"eligible": eligible}))
        regression = root / "regression.json"; regression.write_text(json.dumps({"passed": passed}))
        return root, candidate, production, approval, regression

    def test_failed_production_regression_is_non_mutating(self):
        root, candidate, production, approval, regression = self.setup_case(passed=False)
        result = subprocess.run(["python3", str(SCRIPT), "--candidate", str(candidate),
                                 "--production", str(production), "--approval", str(approval),
                                 "--production-api-regression", str(regression)], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertTrue((production / "stale.safetensors").exists())
        self.assertFalse(list(root.glob("production.backup-*")))

    def test_confirmed_switch_is_complete_and_backed_up(self):
        root, candidate, production, approval, regression = self.setup_case()
        result = subprocess.run(["python3", str(SCRIPT), "--candidate", str(candidate),
                                 "--production", str(production), "--approval", str(approval),
                                 "--production-api-regression", str(regression),
                                 "--confirm-production"], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue((production / "new.safetensors").exists())
        self.assertFalse((production / "stale.safetensors").exists())
        self.assertEqual(len(list(root.glob("production.backup-*"))), 1)

if __name__ == "__main__":
    unittest.main()
