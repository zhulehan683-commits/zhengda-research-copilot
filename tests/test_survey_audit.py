import json
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import survey_audit


class SurveyAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'raw_private').mkdir()
        self.data = self.root / 'raw_private/data.csv'
        self.schema = self.root / 'schema.json'
        self.schema.write_text(json.dumps({'id_column': 'id', 'missing_values': ['', 'NA'],
            'variables': {'id': {'type': 'string', 'required': True},
                          'q1': {'type': 'integer', 'min': 1, 'max': 5, 'required': True},
                          'age': {'type': 'number', 'min': 18}}}), encoding='utf-8')

    def audit(self):
        return survey_audit.audit(self.root, 'raw_private/data.csv', 'schema.json')

    def test_clean_csv_is_ready_only_for_review(self):
        self.data.write_text('id,q1,age\na,3,20\nb,4,22\n', encoding='utf-8-sig')
        result = self.audit()
        self.assertEqual(result['status'], 'READY_FOR_REVIEW')
        self.assertEqual(result['row_count'], 2)
        self.assertFalse(result['scientific_validity_verified'])

    def test_invalid_values_and_duplicates_block_without_leaking_values(self):
        self.data.write_text('id,q1,age\nPRIVATE_ID,6,NaN\nPRIVATE_ID,,18\n', encoding='utf-8')
        before = self.data.read_bytes()
        result = self.audit()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['duplicate_id_rows'], 1)
        self.assertEqual(result['variables']['q1']['out_of_range'], 1)
        self.assertEqual(result['variables']['q1']['missing'], 1)
        self.assertEqual(result['variables']['age']['invalid_type'], 1)
        self.assertNotIn('PRIVATE_ID', json.dumps(result))
        self.assertEqual(before, self.data.read_bytes())

    def test_empty_and_ragged_csv_block(self):
        for text in ['id,q1,age\n', 'id,q1,age\na,3\n']:
            with self.subTest(text=text):
                self.data.write_text(text)
                self.assertEqual(self.audit()['status'], 'BLOCKED')

    def test_duplicate_headers_and_missing_schema_columns_rejected(self):
        for text in ['id,q1,q1\na,3,3\n', 'id,age\na,20\n']:
            with self.subTest(text=text):
                self.data.write_text(text)
                with self.assertRaises(ValueError):
                    self.audit()

    def test_invalid_schema_rejected(self):
        self.data.write_text('id,q1,age\na,3,20\n')
        for variables in [{}, {'q1': {'type': 'integer', 'min': 5, 'max': 1}},
                          {'q1': {'type': 'unknown'}}]:
            self.schema.write_text(json.dumps({'variables': variables}))
            with self.subTest(variables=variables), self.assertRaises(ValueError):
                self.audit()

    def test_nonobject_schema_rejected(self):
        self.data.write_text('id,q1,age\na,3,20\n')
        for value in [[], 'text', None, 123]:
            self.schema.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.audit()

    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):
            survey_audit.audit(self.root, '../outside.csv', 'schema.json')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/survey_audit.py'),
            '--project', str(self.root), '--data', 'raw_private/data.csv',
            '--schema', 'schema.json', *args], capture_output=True, text=True, encoding='utf-8')

    def test_cli_blocks_without_altering_input_and_writes_summary(self):
        self.data.write_text('id,q1,age\na,9,21\n')
        original = self.data.read_bytes()
        result = self.run_cli('--output', 'analysis/diagnostics.json')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'BLOCKED')
        self.assertEqual(original, self.data.read_bytes())
        self.assertTrue((self.root / 'analysis/diagnostics.json').is_file())

    def test_cli_refuses_output_over_input(self):
        self.data.write_text('id,q1,age\na,3,21\n')
        original = self.data.read_bytes()
        result = self.run_cli('--output', 'raw_private/data.csv')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(original, self.data.read_bytes())

    def test_cli_cannot_overwrite_state_or_existing_analysis(self):
        self.data.write_text('id,q1,age\na,3,21\n')
        for relative in ['state/project.json', 'analysis/existing.json']:
            target = self.root / relative
            target.parent.mkdir(exist_ok=True)
            target.write_text('{"important": true}')
            result = self.run_cli('--output', relative)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(target.read_text(), '{"important": true}')
