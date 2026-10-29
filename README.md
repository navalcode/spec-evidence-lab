# Spec Evidence Lab

[Español](README.es.md) · [![Checks](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml/badge.svg)](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml)

An original engineering demo that connects a feature specification, acceptance criteria, test results and structured AI proposals. The CLI uses the Python standard library. An optional MCP adapter exposes the same checks over stdio.

## The engineering question

What would let a reviewer distinguish a plausible plan from evidence that covers an explicit contract?

The specification in this lab declares stable requirement and acceptance IDs, expected test identities, allowed paths and non-goals. The checker relates it to supplied JUnit results. The proposal reviewer checks whether a structured plan still references the current specification and stays within its declared scope.

Neither a valid plan nor a passing schema approves a change. Proposal results retain `human_review_required: true`. Test results retain `meaning_review_required: true` because the runner's provenance and the adequacy of the tests still need review.

## Run the working example

Requires Python 3.11 or newer. From this directory:

```sh
python3 -m unittest discover -s tests -v
python3 tools/run_demo_tests.py --output artifacts/demo.xml
python3 -m spec_evidence check --spec examples/offline_catalog/spec.json --junit artifacts/demo.xml
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal.json
```

The bundled catalog tests really execute before their JUnit report is checked. They cover preserving cached data, a first-load failure, recovery, repeated reservations and unknown items. The sample proposal is a synthetic example of structured planning input, not a claim that an external model generated it.

To see a rejected proposal:

```sh
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal-stale.json
```

That command returns exit code **1** and `needs_revision`. `digest --spec ...` computes the canonical specification hash when a reviewed contract changes.

## What is checked

| Input | Checks |
|---|---|
| Specification | Required fields, unique IDs, acceptance criteria, test references, relative scope patterns and duplicate JSON keys. |
| JUnit | Required tests present exactly once; failures, errors and skipped results distinguished; contradictory totals and unassigned failures rejected. |
| Proposal | Current specification hash, requirement/test coverage, relative in-scope paths, duplicate changes and unresolved questions. |

Inputs are bounded to 2 MiB. JSON uses UTF-8, at most 64 nesting levels, finite numbers and integers up to 128 digits. XML DTD/entity declarations are rejected. The supported JUnit shape uses `testsuite`/`testsuites` without a namespace and testcase `classname` plus `name`. The checker computes outcomes from cases and checks declared totals for contradictions. It does not execute commands from JSON, inspect a repository automatically or modify files.

Exit codes: **0** for a consistent result, **1** for failed acceptance or a proposal needing revision, **2** for invalid input.

## Language and project preferences

The default JSON report stays unchanged. To add an optional human summary, use `--language en|es` or a bounded JSON preferences file containing only `language`. An explicit flag overrides the file:

```sh
python3 -m spec_evidence check --spec examples/offline_catalog/spec.json --junit artifacts/demo.xml --config examples/preferences.es.json
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal.json --config examples/preferences.es.json --language en
```

The added `presentation` object contains the language and summary. Machine keys, status values, test identities, exit codes and the specification hash do not change. Unknown configuration fields, duplicate keys, unsupported languages and oversized input fail validation. Diagnostics and MCP responses retain their machine contract; this feature does not translate requirements, judge prose or apply a corporate writing prompt.

## Human review in the terminal

Use `--format text` for a compact result with criterion/test IDs, issue codes and the specification hash. `--language en|es` selects the summary; diagnostic codes and proposal messages retain their English contract. Terminal controls in supplied identifiers are escaped. The default remains JSON for automation, and MCP is unchanged.

```sh
python3 -m spec_evidence check --spec examples/offline_catalog/spec.json --junit artifacts/demo.xml --format text
python3 -m spec_evidence review --spec examples/offline_catalog/spec.json --proposal examples/offline_catalog/proposal-stale.json --format text --language es
python3 -m spec_evidence check --help
```

Text output keeps the same exit codes: 0 for a consistent result, 1 for failed evidence/revision and 2 for invalid input. A passing text summary still requires review of evidence provenance and test adequacy. See [presentation decisions](DESIGN.md).

## Optional MCP server

The official Python MCP SDK is pinned in the optional dependency group:

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[mcp]'
.venv/bin/python tools/run_demo_tests.py --output artifacts/demo.xml
.venv/bin/python tools/check_mcp.py
```

The smoke check starts a real server subprocess, negotiates MCP, lists tools, checks structured output, submits valid evidence, rejects a stale plan and observes an invalid-contract tool error. It uses the official SDK client; individual IDE/assistant integrations have not been certified by this check.

Server entry point: `.venv/bin/python -m spec_evidence.mcp_server`. Tools:

- `check_acceptance(spec_json, junit_xml)`
- `review_ai_proposal(spec_json, proposal_json)`

Both tools accept **contents**, not filesystem paths. They have read-only, idempotent annotations, use no model API or credentials and expose no filesystem or command-execution tool. They do not listen on a network port.

## Read the implementation

- [`contracts.py`](spec_evidence/contracts.py): contract validation and canonical hash.
- [`evidence.py`](spec_evidence/evidence.py): acceptance-to-test traceability.
- [`proposals.py`](spec_evidence/proposals.py): structured planning review.
- [`mcp_server.py`](spec_evidence/mcp_server.py): optional protocol adapter.
- [`tests/`](tests/): positive and negative behavior checks.
- [`examples/offline_catalog/`](examples/offline_catalog/): original fixture, contract and proposals.

Validation covers 44 checker/configuration/presentation tests, five bundled behavior tests and four MCP protocol checks. This is a focused example of spec-driven engineering and tool integration. It does not attest the authenticity of arbitrary reports, prove arbitrary requirements correct or measure an AI model's productivity.

Local validation used Python 3.14. [GitHub Actions passed on Python 3.11 and 3.14](https://github.com/navalcode/spec-evidence-lab/actions/runs/40882781413), including the MCP smoke check on 3.14. The badge links to current workflow results.

Reference for the optional adapter: [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).

## License

Original source and documentation: [MIT](LICENSE), copyright 2026 Manuel Naval. Third-party dependencies keep their own licenses.

The terminal presentation increment passes all 44 checker tests locally; prior CI links above describe their recorded revision. Current workflow results are available from the badge.
