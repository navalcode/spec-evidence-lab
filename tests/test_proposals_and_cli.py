from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from spec_evidence import ContractError, review_proposal, spec_digest
from spec_evidence.contracts import expected_tests
from test_contracts_and_evidence import fixture, junit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def proposal(spec):
    ids = [r["id"] for r in spec["requirements"]]
    return {"spec_sha256": spec_digest(spec), "summary": "Implement the offline catalog contract.",
            "requirements": ids, "changes": [{"path": "catalog.py", "requirements": ids,
            "reason": "Preserve cached data and enforce repeatable local bookings."}],
            "planned_tests": sorted(expected_tests(spec)), "open_questions": []}


class ProposalTests(unittest.TestCase):
    def setUp(self):self.spec = fixture();self.plan = proposal(self.spec)

    def codes(self):return {i["code"] for i in review_proposal(self.spec, self.plan)["issues"]}

    def test_valid_proposal_is_ready_for_human_review_and_never_executed(self):
        result = review_proposal(self.spec, self.plan)
        self.assertEqual("ready_for_human_review", result["status"])
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["executed_changes"])

    def test_old_specification_is_detected(self):
        self.plan["spec_sha256"] = "0" * 64
        self.assertIn("stale_spec", self.codes())

    def test_unknown_requirement_in_a_change_is_detected(self):
        self.plan["changes"][0]["requirements"].append("OTHER-REQ")
        self.assertIn("unknown_requirement", self.codes())

    def test_missing_acceptance_test_is_detected(self):
        self.plan["planned_tests"].pop()
        self.assertIn("test_coverage", self.codes())

    def test_path_traversal_absolute_windows_and_outside_scope_are_rejected(self):
        for path in ["../private.txt", "/tmp/file", "C:\\secrets.txt", "other.py", "folder/../catalog.py", "catalog.py\n"]:
            with self.subTest(path=path):
                self.plan["changes"][0]["path"] = path
                self.assertIn("path_out_of_scope", self.codes())

    def test_unresolved_questions_prevent_readiness(self):
        self.plan["open_questions"] = ["Which offline behavior should be implemented?"]
        self.assertIn("unresolved_questions", self.codes())

    def test_duplicate_path_is_detected(self):
        self.plan["changes"].append(deepcopy(self.plan["changes"][0]))
        self.assertIn("duplicate_path", self.codes())

    def test_executable_instructions_are_not_part_of_the_schema(self):
        self.plan["commands"] = ["do-not-execute-this"]
        with self.assertRaises(ContractError):review_proposal(self.spec, self.plan)


class CliTests(unittest.TestCase):
    def test_failed_evidence_returns_one_and_machine_readable_json(self):
        spec = fixture();test = sorted(expected_tests(spec))[0]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);(root/"spec.json").write_text(json.dumps(spec));(root/"report.xml").write_bytes(ET.tostring(junit(spec, {test: "failure"})))
            result = subprocess.run([sys.executable, "-m", "spec_evidence", "check", "--spec", str(root/"spec.json"), "--junit", str(root/"report.xml")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertEqual("failed", json.loads(result.stdout)["status"])

    def test_invalid_input_returns_two_without_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d);(root/"spec.json").write_text('{"schema_version": 1, "schema_version": 2}')
            result = subprocess.run([sys.executable, "-m", "spec_evidence", "digest", "--spec", str(root/"spec.json")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertEqual("invalid_input", json.loads(result.stdout)["status"])
            self.assertNotIn("Traceback", result.stderr)
