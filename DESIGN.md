# Terminal presentation

`--format text` presents the project, stable result status and an explanation, followed by acceptance criteria or proposal issues and the canonical specification hash. Missing, skipped and failed tests keep their IDs and status codes. Proposal issues keep their codes and explain which field to revise. A proposal that passes these checks still needs human review.

The text describes what the supplied report says. It asks the reader to check its provenance and what the tests verify; it does not count a passing test as proof that an arbitrary requirement is correct. A failed result identifies the affected criteria/tests and asks for a fresh JUnit report. The tool never runs proposed changes.

JSON remains the default, with stable machine keys and exit codes. `--language en|es` or a language config selects human summaries; proposal guidance is localized in text mode. Contract diagnostics and supplied IDs retain their technical wording. Non-printable characters in text are escaped. Long identifiers wrap in the reader’s terminal and are not truncated.

[Verification](docs/VERIFICATION.md) records the current commands, machine-output comparison, negative cases and MCP checks. Terminal typography, contrast and wrapping belong to the reader’s terminal; the tool requires no colors or graphical interface.
