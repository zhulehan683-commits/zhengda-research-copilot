#!/usr/bin/env python3
"""Offline installer: one canonical skill plus explicitly selected agent adapters."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path

NAME = 'zhengda-research-copilot'
MANIFEST = '.skill-install.json'
FILES = ('SKILL.md', 'README.md', 'CODEX_START.md', 'install.py', 'install.ps1',
         'THIRD_PARTY_NOTICES.md', 'LICENSE-DECISION.md', 'SECURITY.md',
         'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE')
DIRECTORIES = ('scripts', 'references', 'templates', 'competitions', 'licenses', 'agents', 'docs',
               '.agents/skills')
REQUIRED = ('SKILL.md', 'scripts/workflow.py', 'scripts/task_queue.py',
            'scripts/survey_audit.py', 'scripts/common.py', 'scripts/score_review.py',
            'references/stages.md', 'references/gates.md',
            'competitions/zhengda-17/rules.json', 'THIRD_PARTY_NOTICES.md',
            '.agents/skills/grill-me/SKILL.md', '.agents/skills/grilling/SKILL.md',
            '.agents/skills/find-skills/SKILL.md',
            'references/upstream-skills/grill-me/SKILL.md',
            'references/upstream-skills/grilling/SKILL.md',
            'references/upstream-skills/find-skills/SKILL.md',
            'licenses/mattpocock-skills/LICENSE', 'licenses/vercel-labs-skills/LICENSE')


def linked(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) &
                                     getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def payload(source: Path) -> list[Path]:
    paths = [source / name for name in FILES if (source / name).exists()]
    for name in DIRECTORIES:
        folder = source / name
        ancestor = folder.parent
        while ancestor != source and ancestor != ancestor.parent:
            if linked(ancestor):
                raise ValueError('Linked payload ancestor: ' + str(ancestor))
            ancestor = ancestor.parent
        if linked(folder):
            raise ValueError('Linked payload directory: ' + str(folder))
        if not folder.exists():
            continue
        for parent, dirs, files in os.walk(folder, followlinks=False):
            dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git')]
            for entry in dirs + files:
                if linked(Path(parent) / entry):
                    raise ValueError('Linked payload entry: ' + str(Path(parent) / entry))
            paths.extend(Path(parent) / f for f in files if not f.endswith(('.pyc', '.pyo')))
    for path in paths:
        if linked(path) or not path.is_file():
            raise ValueError('Payload must contain regular files: ' + str(path))
    if not all((source / name) in paths for name in REQUIRED):
        raise ValueError('Incomplete skill distribution; extract the full repository')
    return sorted(paths)


def verify(target: Path) -> dict:
    errors = []
    try:
        data = json.loads((target / MANIFEST).read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('name') != NAME or not isinstance(data.get('files'), dict):
            raise ValueError('Invalid install manifest')
        for name in REQUIRED:
            if name not in data['files']:
                errors.append('Required file not registered: ' + name)
        for rel, expected in data['files'].items():
            candidate = target / rel
            if (Path(rel).is_absolute() or '..' in Path(rel).parts or
                    not candidate.resolve().is_relative_to(target.resolve())):
                errors.append('Unsafe manifest path: ' + rel)
                continue
            cursor = target
            for part in Path(rel).parts:
                cursor = cursor / part
                if linked(cursor):
                    errors.append('Linked manifest entry: ' + rel)
                    break
            else:
                if not candidate.is_file() or digest(candidate) != expected:
                    errors.append('Missing or changed: ' + rel)
        return {'ok': not errors, 'target': str(target), 'files': len(data['files']), 'errors': errors}
    except (OSError, ValueError, TypeError) as exc:
        return {'ok': False, 'target': str(target), 'errors': [str(exc)]}


def make_link(path: Path, target: Path):
    if os.name == 'nt':
        env = {**os.environ, 'SURVEY_LINK_PATH': str(path), 'SURVEY_LINK_TARGET': str(target)}
        subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                        "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                        '-Path $env:SURVEY_LINK_PATH -Target $env:SURVEY_LINK_TARGET | Out-Null'],
                       env=env, check=True, capture_output=True, text=True)
    else:
        path.symlink_to(target, target_is_directory=True)


def remove_staging(path: Path):
    # Only transaction-created staging paths are passed here; never follow a link.
    if linked(path):
        if path.is_symlink():
            path.unlink()
        else:
            path.rmdir()
    elif path.exists():
        shutil.rmtree(path)


def install(source: Path, canonical_root: Path, *, agent_roots=(), mode='link',
            force=False, dry_run=False) -> dict:
    source = source.expanduser().resolve()
    canonical = canonical_root.expanduser().resolve() / NAME
    targets = [canonical]
    for root in agent_roots:
        target = Path(root).expanduser().resolve() / NAME
        if target not in targets:
            targets.append(target)
    if mode not in ('link', 'copy'):
        raise ValueError('mode must be link or copy')
    for target in targets:
        if target == source or target.is_relative_to(source) or source.is_relative_to(target):
            raise ValueError('Installation and source must not overlap: ' + str(target))
    for i, target in enumerate(targets):
        for other in targets[i + 1:]:
            if target.is_relative_to(other) or other.is_relative_to(target):
                raise ValueError('Installation targets must not overlap')
    sources = payload(source)
    skip = set()
    for target in targets:
        if target != canonical and mode == 'link' and linked(target) and target.resolve() == canonical:
            skip.add(target)
        elif os.path.lexists(target) and not force:
            raise FileExistsError('Skill already exists; review before --force: ' + str(target))
    result = {'ok': True, 'canonical': str(canonical), 'mode': mode,
              'targets': [str(t) for t in targets], 'backup': None, 'backups': [],
              'dry_run': dry_run, 'agent_runtime_verified': False}
    if dry_run:
        return result
    manifest = {'name': NAME, 'schema': 1,
                'files': {p.relative_to(source).as_posix(): digest(p) for p in sources}}
    staged = {}
    replaced = []
    backups = {}
    token = uuid.uuid4().hex
    try:
        for target in targets:
            if target in skip:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            staging = target.with_name('.zrc-' + token[:12])
            staged[target] = staging
            if target == canonical or mode == 'copy':
                staging.mkdir()
                for src in sources:
                    dst = staging / src.relative_to(source)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, dst)
                (staging / MANIFEST).write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
                if not verify(staging)['ok']:
                    raise ValueError('Staging validation failed')
        for target, staging in staged.items():
            # Windows Junction creation requires the canonical target to exist.
            if target != canonical and mode == 'link':
                make_link(staging, canonical)
            if os.path.lexists(target):
                backup = target.parent.parent / '.skill-backups' / token[:12]
                backup.parent.mkdir(parents=True, exist_ok=True)
                if os.path.lexists(backup):
                    backup = backup.with_name(uuid.uuid4().hex[:12])
                target.rename(backup)
                backups[target] = backup
            staging.rename(target)
            replaced.append(target)
        result['backups'] = [str(p) for p in backups.values()]
        result['backup'] = str(backups[canonical]) if canonical in backups else None
        result['verification'] = [verify(target) for target in targets]
        if not all(v['ok'] for v in result['verification']):
            raise ValueError('Installed payload verification failed')
        return result
    except Exception:
        for target in reversed(replaced):
            remove_staging(target)
        for target, backup in backups.items():
            backup.rename(target)
        raise
    finally:
        for path in staged.values():
            if os.path.lexists(path):
                remove_staging(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-root', type=Path, default=Path.home() / '.agents/skills',
                        help='Canonical skills directory, including a D: directory if preferred')
    parser.add_argument('--agent-root', type=Path, action='append', default=[],
                        help='Additional agent skills directory; repeat for multiple agents')
    parser.add_argument('--mode', choices=['link', 'copy'], default='link')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verify', action='store_true', help='Read-only install hash verification')
    args = parser.parse_args()
    try:
        if args.verify:
            targets = [root.expanduser().resolve() / NAME for root in [args.target_root, *args.agent_root]]
            results = [verify(t) for t in targets]
            result = {'ok': all(v['ok'] for v in results), 'verification': results,
                      'agent_runtime_verified': False}
        else:
            result = install(Path(__file__).parent, args.target_root, agent_roots=args.agent_root,
                             mode=args.mode, force=args.force, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['ok'] else 2
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
