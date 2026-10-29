# Terminal presentation

Spec Evidence is a CLI/MCP tool. Its visual surface is a plain terminal report and structured data, not a dashboard. Terminal fonts, size, theme and accessibility remain under the reader's control. No ANSI, motion, browser, color-only status or added package is required.

Use `--format text` for human review. Read top to bottom: project and stable status, a short explanation, acceptance criteria or proposal issues, and canonical specification hash. Failed/missing/skipped tests retain identifiers and machine status; proposal issues retain their codes. A consistent result still requires evidence provenance/test adequacy review. A valid proposal executes nothing.

JSON is the default and retains its schema/exit codes. Language preferences select EN/ES summaries without translating machine keys, supplied IDs or technical issue messages. Non-printable characters from supplied identifiers are escaped in text mode. Native terminal wrapping handles long IDs; do not truncate evidence.

Verification covers failed/missing evidence, stale proposals, invalid input, unchanged default JSON and hash, language precedence and terminal-control escaping. Command transcripts represent actual executions, never generated screen mockups.
