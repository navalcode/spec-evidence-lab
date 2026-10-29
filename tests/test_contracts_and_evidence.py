from copy import deepcopy
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from spec_evidence import ContractError, check_results, load_json, spec_digest, validate_spec
from spec_evidence.contracts import expected_tests

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return load_json((ROOT / "examples/offline_catalog/spec.json").read_bytes())


def junit(spec, outcomes=None):
    outcomes = outcomes or {}
    root = ET.Element("testsuite")
    for identifier in sorted(expected_tests(spec)):
        if outcomes.get(identifier) == "missing":
            continue
        classname, name = identifier.rsplit(".", 1)
        case = ET.SubElement(root, "testcase", {"classname": classname, "name": name})
        if identifier in outcomes:
            ET.SubElement(case, outcomes[identifier])
    return root


class ContractTests(unittest.TestCase):
    def test_canonical_digest_is_independent_of_object_key_order(self):
        spec = fixture()
        reordered = dict(reversed(list(spec.items())))
        self.assertEqual(spec_digest(spec), spec_digest(reordered))

    def test_changed_acceptance_changes_spec_digest(self):
        spec = fixture();changed = deepcopy(spec)
        changed["requirements"][0]["acceptance"][0]["description"] += " with a visible stale state"
        self.assertNotEqual(spec_digest(spec), spec_digest(changed))

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(ContractError, "Duplicate"):
            load_json('{"schema_version": 1, "schema_version": 2}')

    def test_nonfinite_numbers_are_rejected(self):
        for number in ['NaN', 'Infinity', '1e9999']:
            with self.subTest(number=number), self.assertRaises(ContractError):
                load_json('{"value":' + number + '}')

    def test_extreme_integer_is_an_input_error(self):
        with self.assertRaises(ContractError):
            load_json('{"value":' + '9' * 10_000 + '}')

    def test_extreme_nesting_is_an_input_error(self):
        with self.assertRaises(ContractError):
            load_json('[' * 10_000 + '0' + ']' * 10_000)
        self.assertEqual('[' * 100, load_json('"' + '[' * 100 + '"'))

    def test_boolean_is_not_a_schema_version(self):
        spec = fixture();spec["schema_version"] = True
        with self.assertRaises(ContractError):validate_spec(spec)

    def test_duplicate_acceptance_identifier_is_rejected(self):
        spec = fixture();spec["requirements"][1]["acceptance"][0]["id"] = "AC-CACHE"
        with self.assertRaises(ContractError):validate_spec(spec)

    def test_requirement_without_acceptance_is_rejected(self):
        spec = fixture();spec["requirements"][0]["acceptance"] = []
        with self.assertRaises(ContractError):validate_spec(spec)

    def test_scope_cannot_escape_the_project(self):
        spec = fixture();spec["scope"]["paths"] = ["../private/**"]
        with self.assertRaises(ContractError):validate_spec(spec)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.spec = fixture()
        self.test_id = sorted(expected_tests(self.spec))[0]

    def check(self, root):
        return check_results(self.spec, ET.tostring(root))

    def test_all_declared_cases_pass_but_meaning_still_requires_review(self):
        report = self.check(junit(self.spec))
        self.assertEqual("passed", report["status"])
        self.assertEqual(5, len(report["criteria"]))
        self.assertTrue(report["meaning_review_required"])

    def test_missing_case_cannot_satisfy_acceptance(self):
        report = self.check(junit(self.spec, {self.test_id: "missing"}))
        self.assertEqual("failed", report["status"])
        self.assertTrue(any(t["status"] == "missing" for c in report["criteria"] for t in c["tests"]))

    def test_skipped_case_cannot_satisfy_acceptance(self):
        self.assertEqual("failed", self.check(junit(self.spec, {self.test_id: "skipped"}))["status"])

    def test_failed_case_cannot_satisfy_acceptance(self):
        self.assertEqual("failed", self.check(junit(self.spec, {self.test_id: "failure"}))["status"])

    def test_failure_outside_traceability_still_fails_the_suite(self):
        root = junit(self.spec)
        case = ET.SubElement(root, "testcase", {"classname": "Other", "name": "test_regression"})
        ET.SubElement(case, "failure")
        report = self.check(root)
        self.assertEqual("failed", report["status"])
        self.assertEqual(["Other.test_regression"], report["suite_failures"])

    def test_duplicate_case_is_ambiguous_and_rejected(self):
        root = junit(self.spec);root.append(deepcopy(root[0]))
        with self.assertRaisesRegex(ContractError, "Duplicate"):self.check(root)

    def test_claimed_success_totals_cannot_hide_failed_case(self):
        root = junit(self.spec, {self.test_id: "failure"});root.set("failures", "0")
        with self.assertRaisesRegex(ContractError, "contradict"):self.check(root)

    def test_undeclared_suite_initialization_error_is_rejected(self):
        root = junit(self.spec);ET.SubElement(root, "error")
        with self.assertRaises(ContractError):self.check(root)

    def test_notrun_attribute_is_treated_as_skipped(self):
        root = junit(self.spec);root[0].set("status", "notrun")
        self.assertEqual("failed", self.check(root)["status"])

    def test_conflicting_outcomes_are_rejected(self):
        root = junit(self.spec);ET.SubElement(root[0], "failure");ET.SubElement(root[0], "skipped")
        with self.assertRaises(ContractError):self.check(root)

    def test_unknown_status_is_not_assumed_to_mean_passed(self):
        root = junit(self.spec);root[0].set("status", "pending")
        with self.assertRaises(ContractError):self.check(root)

    def test_dtd_is_rejected_in_utf8_and_utf16(self):
        xml = '<!DOCTYPE testsuite [<!ENTITY item "value">]><testsuite/>'
        for encoding in ["utf-8", "utf-16"]:
            with self.subTest(encoding=encoding), self.assertRaises(ContractError):
                check_results(self.spec, xml.encode(encoding))

    def test_empty_report_is_not_evidence(self):
        with self.assertRaises(ContractError):self.check(ET.Element("testsuite"))

    def test_oversized_input_is_rejected(self):
        with self.assertRaises(ContractError):check_results(self.spec, b"x" * (2 * 1024 * 1024 + 1))
