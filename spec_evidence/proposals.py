"""Review the shape and declared scope of an AI proposal; never execute it."""

from fnmatch import fnmatchcase
from .contracts import (ContractError, expected_tests, object_fields, relative_path,
                        spec_digest, string_list, text, validate_spec)


def review_proposal(spec, proposal):
    validate_spec(spec)
    object_fields(proposal, {"spec_sha256", "summary", "requirements", "changes", "planned_tests", "open_questions"}, "proposal")
    text(proposal["summary"], "proposal.summary")
    string_list(proposal["requirements"], "proposal.requirements")
    string_list(proposal["planned_tests"], "proposal.planned_tests")
    string_list(proposal["open_questions"], "proposal.open_questions", empty=True)
    if not isinstance(proposal["changes"], list) or not proposal["changes"]:
        raise ContractError("Proposal needs at least one declared change")
    issues = []
    known = {req["id"] for req in spec["requirements"]}
    required_tests = expected_tests(spec)
    if proposal["spec_sha256"] != spec_digest(spec):
        issues.append({"code": "stale_spec", "message": "Proposal does not reference the current specification."})
    if set(proposal["requirements"]) != known:
        issues.append({"code": "requirement_coverage", "message": "Proposal must reference exactly the declared requirements."})
    if set(proposal["planned_tests"]) != required_tests:
        issues.append({"code": "test_coverage", "message": "Planned tests must match the current acceptance contract."})
    covered = set()
    paths = set()
    for change in proposal["changes"]:
        object_fields(change, {"path", "requirements", "reason"}, "change")
        string_list(change["requirements"], "change.requirements")
        text(change["reason"], "change.reason")
        path = change["path"]
        if not relative_path(path) or not any(fnmatchcase(path, pattern) for pattern in spec["scope"]["paths"]):
            issues.append({"code": "path_out_of_scope", "message": "A proposed path is not within the declared scope."})
        if isinstance(path, str):
            if path in paths:
                issues.append({"code": "duplicate_path", "message": "A path is declared more than once."})
            paths.add(path)
        if not set(change["requirements"]) <= known:
            issues.append({"code": "unknown_requirement", "message": "A change references an unknown requirement."})
        covered.update(change["requirements"])
    if not known <= covered:
        issues.append({"code": "unplanned_requirement", "message": "Some requirements have no proposed change."})
    if proposal["open_questions"]:
        issues.append({"code": "unresolved_questions", "message": "The proposal still contains unresolved questions."})
    return {"project": spec["project"], "spec_sha256": spec_digest(spec),
            "status": "needs_revision" if issues else "ready_for_human_review",
            "issues": issues, "human_review_required": True, "executed_changes": False}
