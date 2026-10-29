"""Validate explicit feature contracts; parsing never executes input content."""

import hashlib
import json
import math
from pathlib import PurePosixPath
import re

MAX_INPUT_BYTES = 2 * 1024 * 1024
ID = re.compile(r"[A-Z][A-Z0-9_-]{1,63}\Z")


class ContractError(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("Duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ContractError("Non-finite JSON number")


def _bounded_integer(value):
    if len(value.lstrip("-")) > 128:
        raise ContractError("JSON integer exceeds 128 digits")
    return int(value)


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ContractError("Non-finite JSON number")
    return number


def _check_nesting(data):
    depth = 0
    quoted = False
    escaped = False
    for char in data:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > 64:
                raise ContractError("JSON nesting exceeds 64 levels")
        elif char in "]}":
            depth -= 1


def load_json(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, bytes) or len(data) > MAX_INPUT_BYTES:
        raise ContractError("JSON input must be at most 2 MiB")
    try:
        decoded = data.decode("utf-8-sig")
        _check_nesting(decoded)
        return json.loads(decoded, object_pairs_hook=_unique_object, parse_constant=_reject_constant,
                          parse_int=_bounded_integer, parse_float=_finite_float)
    except ContractError:
        raise
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise ContractError("Invalid JSON input") from exc


def object_fields(value, required, label, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys():
        raise ContractError(f"{label}: missing required fields or not an object")
    if value.keys() - set(required) - set(optional):
        raise ContractError(f"{label}: unknown fields")


def text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 10_000:
        raise ContractError(f"{label}: expected a non-empty bounded string")


def string_list(value, label, empty=False):
    if not isinstance(value, list) or (not value and not empty):
        raise ContractError(f"{label}: expected a list")
    for item in value:
        text(item, label)
    if len(set(value)) != len(value):
        raise ContractError(f"{label}: duplicate entries")


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        return False
    if any(ord(c) < 32 for c in value) or value.startswith("/"):
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts) and not PurePosixPath(value).is_absolute()


def validate_spec(spec):
    object_fields(spec, {"schema_version", "project", "objective", "scope", "requirements", "non_goals"}, "spec")
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ContractError("Unsupported schema version")
    text(spec["project"], "project")
    text(spec["objective"], "objective")
    string_list(spec["non_goals"], "non_goals", empty=True)
    object_fields(spec["scope"], {"paths"}, "scope")
    string_list(spec["scope"]["paths"], "scope.paths")
    if not all(relative_path(path) for path in spec["scope"]["paths"]):
        raise ContractError("Scope patterns must be relative paths without traversal")
    if not isinstance(spec["requirements"], list) or not spec["requirements"]:
        raise ContractError("At least one requirement is required")
    ids = set()
    for requirement in spec["requirements"]:
        object_fields(requirement, {"id", "statement", "acceptance"}, "requirement")
        _new_id(requirement["id"], ids)
        text(requirement["statement"], "requirement.statement")
        if not isinstance(requirement["acceptance"], list) or not requirement["acceptance"]:
            raise ContractError("Each requirement needs acceptance criteria")
        for criterion in requirement["acceptance"]:
            object_fields(criterion, {"id", "description", "tests"}, "acceptance")
            _new_id(criterion["id"], ids)
            text(criterion["description"], "acceptance.description")
            string_list(criterion["tests"], "acceptance.tests")
    return spec


def _new_id(value, known):
    if not isinstance(value, str) or not ID.fullmatch(value) or value in known:
        raise ContractError("Requirement and criterion IDs must be unique stable identifiers")
    known.add(value)


def spec_digest(spec):
    validate_spec(spec)
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def expected_tests(spec):
    return {test for req in spec["requirements"] for ac in req["acceptance"] for test in ac["tests"]}
