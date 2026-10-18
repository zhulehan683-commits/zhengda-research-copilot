import importlib.util
import json
import tempfile
import shutil
import os
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('skill_install', ROOT / 'install.py')
        self.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.installer)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.target = self.base / 'shared' / self.installer.NAME

    def install(self, **kwargs):
        return self.installer.install(ROOT, self.target.parent, **kwargs)

    def test_minimal_payload_and_verified_hashes(self):
        self.install()
        for name in ['SKILL.md', 'scripts/workflow.py', 'scripts/survey_audit.py',
                     'references/stages.md', 'competitions/zhengda-17/rules.json',
                     'THIRD_PARTY_NOTICES.md', 'licenses']:
            self.assertTrue((self.target / name).exists(), name)
        self.assertFalse((self.target / '.git').exists())
        self.assertFalse((self.target / 'tests/test_install.py').exists())
        self.assertTrue(self.installer.verify(self.target)['ok'])

    def test_reinstall_requires_force_and_preserves_backup(self):
        self.install()
        (self.target / 'local-note.txt').write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            self.install()
        result = self.install(force=True)
        self.assertEqual((Path(result['backup']) / 'local-note.txt').read_text(), 'keep')
        self.assertTrue(self.installer.verify(self.target)['ok'])

    def test_detects_changed_and_missing_payload(self):
        self.install()
        (self.target / 'SKILL.md').write_text('changed', encoding='utf-8')
        (self.target / 'scripts/workflow.py').unlink()
        self.assertFalse(self.installer.verify(self.target)['ok'])

    def test_nested_install_and_source_install_are_rejected(self):
        with self.assertRaises(ValueError):
            self.installer.install(self.base / self.installer.NAME, self.base)
        with self.assertRaises(ValueError):
            self.installer.install(ROOT, ROOT / 'nested')

    def test_copy_adapter_contains_same_payload(self):
        adapter = self.base / 'agent' / self.installer.NAME
        self.install(agent_roots=[adapter.parent], mode='copy')
        self.assertTrue(self.installer.verify(adapter)['ok'])
        self.assertFalse(adapter.is_symlink())
        self.assertEqual((self.target / 'SKILL.md').read_bytes(), (adapter / 'SKILL.md').read_bytes())

    def test_adapter_conflict_is_preflighted_before_update(self):
        adapter = self.base / 'agent' / self.installer.NAME
        adapter.mkdir(parents=True)
        (adapter / 'unrelated.txt').write_text('keep')
        with self.assertRaises(FileExistsError):
            self.install(agent_roots=[adapter.parent])
        self.assertFalse(self.target.exists())
        self.assertEqual((adapter / 'unrelated.txt').read_text(), 'keep')

    def test_dry_run_does_not_create_paths(self):
        self.install(dry_run=True, agent_roots=[self.base / 'agent'])
        self.assertFalse(self.target.parent.exists())

    def test_manifest_cannot_escape_installation(self):
        self.install()
        manifest = self.target / '.skill-install.json'
        data = json.loads(manifest.read_text())
        data['files']['../outside'] = '0' * 64
        manifest.write_text(json.dumps(data))
        self.assertFalse(self.installer.verify(self.target)['ok'])

    def test_link_adapter_resolves_to_canonical_and_survives_update(self):
        adapter = self.base / 'agent' / self.installer.NAME
        self.install(agent_roots=[adapter.parent])
        self.assertTrue(self.installer.linked(adapter))
        self.assertEqual(adapter.resolve(), self.target)
        self.install(agent_roots=[adapter.parent], force=True)
        self.assertTrue(self.installer.verify(adapter)['ok'])
        adapter.rmdir() if not adapter.is_symlink() else adapter.unlink()

    def test_rollback_restores_old_canonical_on_adapter_failure(self):
        self.install()
        (self.target / 'note.txt').write_text('previous version')
        adapter = self.base / 'agent' / self.installer.NAME
        original_rename = Path.rename
        def fail_adapter(path, destination):
            if path.name.startswith('.zrc-') and Path(destination) == adapter:
                raise OSError('injected adapter failure')
            return original_rename(path, destination)
        with mock.patch.object(Path, 'rename', fail_adapter):
            with self.assertRaises(OSError):
                self.install(agent_roots=[adapter.parent], mode='copy', force=True)
        self.assertEqual((self.target / 'note.txt').read_text(), 'previous version')
        self.assertFalse(adapter.exists())
        self.assertFalse(list(self.target.parent.glob('.zrc-*')))

    def test_install_without_windows_stat_constants(self):
        with mock.patch.object(self.installer.stat, 'FILE_ATTRIBUTE_REPARSE_POINT', create=True):
            delattr(self.installer.stat, 'FILE_ATTRIBUTE_REPARSE_POINT')
            self.install()
            self.assertTrue(self.installer.verify(self.target)['ok'])

    def test_missing_runtime_dependency_rejected(self):
        source = self.base / 'source'
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        (source / 'scripts/common.py').unlink()
        with self.assertRaises(ValueError):
            self.installer.install(source, self.target.parent)

    def test_nonobject_manifest_returns_structured_failure(self):
        self.install()
        for value in [[], 'text', None, 123]:
            (self.target / '.skill-install.json').write_text(json.dumps(value))
            with self.subTest(value=value):
                self.assertFalse(self.installer.verify(self.target)['ok'])

    @unittest.skipUnless(os.name == 'nt', 'Windows path-length regression')
    def test_staging_is_shorter_than_final_path(self):
        longest = max(self.installer.payload(ROOT), key=lambda p: len(str(p.relative_to(ROOT))))
        relative = longest.relative_to(ROOT)
        padding = 235 - len(str(self.base / 'skills' / self.installer.NAME / relative)) - 1
        self.assertGreater(padding, 0)
        target_root = self.base / ('p' * padding) / 'skills'
        result = self.installer.install(ROOT, target_root)
        self.assertTrue(self.installer.verify(Path(result['canonical']))['ok'])
