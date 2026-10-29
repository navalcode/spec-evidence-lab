import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from spec_evidence.__main__ import main
from spec_evidence.contracts import MAX_INPUT_BYTES, expected_tests
from test_contracts_and_evidence import fixture, junit
from test_proposals_and_cli import proposal


class PresentationTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        self.root=Path(folder.name);self.spec=fixture()
        (self.root/'spec.json').write_text(json.dumps(self.spec))
        (self.root/'config.json').write_text('{"language":"es"}')
        (self.root/'report.xml').write_bytes(ET.tostring(junit(self.spec)))
        (self.root/'proposal.json').write_text(json.dumps(proposal(self.spec)))

    def invoke(self, command='check', *extra):
        args=[command,'--spec',str(self.root/'spec.json')]
        if command=='check':args+=['--junit',str(self.root/'report.xml')]
        if command=='review':args+=['--proposal',str(self.root/'proposal.json')]
        out=io.StringIO()
        with contextlib.redirect_stdout(out):code=main(args+list(extra))
        return code,json.loads(out.getvalue())

    def test_default_machine_report_is_preserved_and_spanish_summary_is_opt_in(self):
        code,baseline=self.invoke();self.assertEqual(0,code);self.assertNotIn('presentation',baseline)
        code,localized=self.invoke('check','--config',str(self.root/'config.json'))
        summary=localized.pop('presentation')
        self.assertEqual(baseline,localized);self.assertEqual('es',summary['language'])
        self.assertIn('procedencia',summary['summary'])

    def test_failed_evidence_keeps_exit_code_and_status_in_both_languages(self):
        identifier=sorted(expected_tests(self.spec))[0]
        (self.root/'report.xml').write_bytes(ET.tostring(junit(self.spec,{identifier:'failure'})))
        for language in ['en','es']:
            code,result=self.invoke('check','--language',language)
            self.assertEqual(1,code);self.assertEqual('failed',result['status'])
            self.assertEqual(language,result['presentation']['language'])

    def test_command_line_language_overrides_project_configuration(self):
        code,result=self.invoke('check','--config',str(self.root/'config.json'),'--language','en')
        self.assertEqual(0,code);self.assertEqual('en',result['presentation']['language'])
        self.assertIn('provenance',result['presentation']['summary'])

    def test_language_cannot_change_specification_digest(self):
        _,baseline=self.invoke('digest')
        for language in ['en','es']:
            code,result=self.invoke('digest','--language',language)
            self.assertEqual(0,code);self.assertEqual(baseline['spec_sha256'],result['spec_sha256'])
            self.assertEqual('digest',result.get('status','digest'))

    def test_localized_proposal_still_requires_human_review_and_executes_nothing(self):
        code,result=self.invoke('review','--config',str(self.root/'config.json'))
        self.assertEqual(0,code);self.assertTrue(result['human_review_required']);self.assertFalse(result['executed_changes'])
        self.assertIn('revisión humana',result['presentation']['summary'])
        (self.root/'proposal.json').write_text(json.dumps({**proposal(self.spec),'spec_sha256':'0'*64}))
        code,result=self.invoke('review','--language','es')
        self.assertEqual(1,code);self.assertEqual('needs_revision',result['status']);self.assertFalse(result['executed_changes'])

    def test_invalid_duplicate_unknown_and_oversized_configuration_fails_closed(self):
        for content in ['[]','{}','{"language":"fr"}','{"language":true}','{"language":"es","instructions":"execute"}','{"language":"es","language":"en"}',' '*(MAX_INPUT_BYTES+1)]:
            with self.subTest(size=len(content)):
                (self.root/'config.json').write_text(content)
                code,result=self.invoke('check','--config',str(self.root/'config.json'),'--language','es')
                self.assertEqual(2,code);self.assertEqual('invalid_input',result['status'])
                self.assertEqual('es',result['presentation']['language'])
