# Verification

Checked on 30 October 2026 on macOS with Python 3.14.2.

```sh
python3 -m unittest discover -s tests -v
python3 tools/run_demo_tests.py --output artifacts/demo.xml
python3 -m spec_evidence check --spec examples/offline_catalog/spec.json --junit artifacts/demo.xml
.venv/bin/python tools/check_mcp.py
```

The validator/configuration/presentation suite passes 44 tests. The catalog runner executes five tests and creates a fresh JUnit report. The optional MCP environment uses the pinned SDK 2.3.0; its four protocol checks pass against a real stdio subprocess. Install that optional environment as described in the README before running the last command.

Terminal checks cover English and Spanish acceptance results, valid and stale proposals, missing tests and invalid preferences. A stale proposal exits 1 and explains how to reread the specification, revise the plan and calculate its digest. Invalid input exits 2. Default JSON from digest, acceptance, valid review and stale review was parsed and compared with the pre-edit results; all four remained equal. Optional translated summaries intentionally change with language.

The [checks workflow](https://github.com/navalcode/spec-evidence-lab/actions/workflows/checks.yml) runs the validator/example checks on Python 3.11 and 3.14 and exercises MCP on 3.14. Its run history is the hosted evidence; the local results above do not establish compatibility with every MCP client.

A consistent report establishes agreement with the supplied contract and test report. It does not authenticate their provenance or establish that the tests sufficiently verify the product. No changes are applied by the proposal reviewer.
