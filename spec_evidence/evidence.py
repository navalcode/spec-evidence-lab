"""Relate a declared contract to supplied JUnit results without trusting totals."""

from collections import Counter
import xml.etree.ElementTree as ET
from .contracts import ContractError, MAX_INPUT_BYTES, spec_digest, validate_spec


def parse_junit(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, bytes) or len(data) > MAX_INPUT_BYTES:
        raise ContractError("JUnit input must be at most 2 MiB")
    # Normalize UTF-16/32 encodings before checking markup declarations.
    declaration_view = data.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in declaration_view or b"<!ENTITY" in declaration_view:
        raise ContractError("DTD and entity declarations are not allowed")
    try:
        root = ET.fromstring(data)
    except (ET.ParseError, ValueError) as exc:
        raise ContractError("Invalid JUnit XML") from exc
    if root.tag not in {"testsuite", "testsuites"}:
        raise ContractError("Expected a JUnit testsuite or testsuites root")
    cases = {}
    for case in root.iter("testcase"):
        name, classname = case.get("name"), case.get("classname")
        if not name or not classname:
            raise ContractError("JUnit cases require name and classname")
        identifier = f"{classname}.{name}"
        if identifier in cases:
            raise ContractError("Duplicate JUnit testcase identifier")
        statuses = [tag for tag in ["failure", "error", "skipped"] if case.find(tag) is not None]
        declared = case.get("status", "run").lower()
        if declared not in {"run", "passed", "success", "notrun", "disabled", "skipped", "failed", "error"}:
            raise ContractError("Unsupported JUnit testcase status")
        if declared in {"notrun", "disabled", "skipped"} and "skipped" not in statuses:
            statuses.append("skipped")
        if declared in {"failed", "error"}:
            outcome = "failure" if declared == "failed" else "error"
            if outcome not in statuses:
                statuses.append(outcome)
        if case.get("result", "").lower() in {"suppressed", "skipped"} and "skipped" not in statuses:
            statuses.append("skipped")
        if len(statuses) > 1:
            raise ContractError("Conflicting JUnit testcase outcomes")
        cases[identifier] = statuses[0] if statuses else "passed"
    if not cases:
        raise ContractError("JUnit contains no testcases")
    for suite in root.iter():
        if suite.tag not in {"testsuite", "testsuites"}:
            continue
        if suite.find("error") is not None or suite.find("failure") is not None:
            raise ContractError("JUnit suite contains an unassigned failure")
        children = list(suite.iter("testcase"))
        counts = Counter(cases[f'{case.get("classname")}.{case.get("name")}'] for case in children)
        actual = {"tests": len(children), "failures": counts["failure"], "errors": counts["error"], "skipped": counts["skipped"]}
        for key, count in actual.items():
            if suite.get(key) is not None and suite.get(key) != str(count):
                raise ContractError("JUnit declared totals contradict its testcases")
    return cases


def check_results(spec, junit):
    validate_spec(spec)
    cases = parse_junit(junit)
    criteria = []
    for req in spec["requirements"]:
        for ac in req["acceptance"]:
            tests = [{"id": identifier, "status": cases.get(identifier, "missing")} for identifier in ac["tests"]]
            criteria.append({"requirement": req["id"], "criterion": ac["id"],
                             "passed": all(t["status"] == "passed" for t in tests), "tests": tests})
    suite_failures = [identifier for identifier, status in cases.items() if status in {"failure", "error"}]
    passed = all(ac["passed"] for ac in criteria) and not suite_failures
    return {"project": spec["project"], "spec_sha256": spec_digest(spec),
            "status": "passed" if passed else "failed", "criteria": criteria,
            "suite_counts": dict(Counter(cases.values())), "suite_failures": suite_failures,
            "meaning_review_required": True,
            "scope": "Consistency with supplied JUnit; runner provenance and test adequacy require review."}
