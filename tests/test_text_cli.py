import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from spec_evidence.__main__ import main
from spec_evidence.contracts import expected_tests
from test_contracts_and_evidence import fixture, junit
from test_proposals_and_cli import proposal


class TextCliTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.spec = fixture()
        (self.root / 'spec.json').write_text(json.dumps(self.spec))
        (self.root / 'report.xml').write_bytes(ET.tostring(junit(self.spec)))
        (self.root / 'proposal.json').write_text(json.dumps(proposal(self.spec)))

    def invoke(self, command, language, *extra):
        args = [command, '--spec', str(self.root / 'spec.json'), '--format', 'text', '--language', language]
        if command == 'check': args += ['--junit', str(self.root / 'report.xml')]
        if command == 'review': args += ['--proposal', str(self.root / 'proposal.json')]
        output = io.StringIO()
        with contextlib.redirect_stdout(output): code = main(args + list(extra))
        return code, output.getvalue()

    def test_failed_acceptance_identifies_the_missing_test_and_preserves_exit_code(self):
        identifier = sorted(expected_tests(self.spec))[0]
        report = junit(self.spec)
        for case in list(report):
            if f'{case.get("classname")}.{case.get("name")}' == identifier: report.remove(case)
        (self.root / 'report.xml').write_bytes(ET.tostring(report))
        for language in ['en', 'es']:
            code, output = self.invoke('check', language)
            self.assertEqual(1, code)
            self.assertIn('failed', output)
            self.assertIn('missing: ' + identifier, output)
            self.assertIn('provenance' if language == 'en' else 'procedencia', output)

    def test_proposal_rejection_shows_issue_code_and_no_execution(self):
        (self.root / 'proposal.json').write_text(json.dumps({**proposal(self.spec), 'spec_sha256': '0' * 64}))
        for language in ['en', 'es']:
            code, output = self.invoke('review', language)
            self.assertEqual(1, code)
            self.assertIn('stale_spec:', output)
            self.assertIn('digest', output)
            self.assertIn('No changes were executed.' if language == 'en' else 'No se ejecutaron cambios.', output)

    def test_digest_and_invalid_input_remain_distinct_from_acceptance(self):
        code, output = self.invoke('digest', 'en')
        self.assertEqual(0, code); self.assertIn('does not execute tests', output)
        (self.root / 'spec.json').write_text('{}')
        code, output = self.invoke('check', 'es')
        self.assertEqual(2, code); self.assertIn('invalid_input', output)

    def test_text_cannot_emit_terminal_escape_or_line_breaks_from_contract_content(self):
        self.spec['project'] = 'demo\x1b[2J\nforged status'
        (self.root / 'spec.json').write_text(json.dumps(self.spec))
        code, output = self.invoke('check', 'en')
        self.assertEqual(0, code)
        self.assertNotIn('\x1b', output)
        self.assertIn('demo\\u001b[2J\\u000aforged status', output)
