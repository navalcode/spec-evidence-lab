# Spec Evidence Lab

[Español](README.es.md) · [![Checks](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml/badge.svg)](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml)

A Python CLI that checks required test IDs against JUnit results and reviews structured change proposals. It identifies missing, failed or skipped tests and proposals that do not match the specification’s hash, requirements, tests or allowed paths.

The specification declares stable IDs, expected tests, allowed paths and non-goals. A passing result describes consistency with those declarations. The reviewer must still check where the test report came from and whether the tests verify the intended behavior. A valid proposal remains subject to human review and executes no changes. The CLI uses the standard library; an optional MCP adapter exposes the same checks over stdio.

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

The added `presentation` object contains the language and summary. Machine keys, status values, test identities, exit codes and the specification hash do not change. Unknown configuration fields, duplicate keys, unsupported languages and oversized input fail validation. Diagnostics and MCP responses retain their machine contract; the language preference only changes the presentation layer.

## Human review in the terminal

Use `--format text` for a compact result with criterion/test IDs, issue codes and the specification hash. `--language en|es` selects the summary; issue codes stay stable, while proposal explanations tell you how to revise each field. Terminal controls in supplied identifiers are escaped. The default remains JSON for automation, and MCP is unchanged.

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

Current checks: **44 validator/configuration/presentation tests, five example tests and four real MCP protocol checks**. [Verification](docs/VERIFICATION.md) records the commands, machine-output comparisons, failure cases and hosted results. The optional adapter uses the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), pinned to 2.3.0.

## License

Original source and documentation: [MIT](LICENSE), copyright 2026 Manuel Naval. Third-party dependencies keep their own licenses.
