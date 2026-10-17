"""Shared local audit primitives. Python >= 3.10; no third-party packages."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def project_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def within(project: Path, file: str, *, must_exist: bool = True) -> Path:
    """Resolve a project-local path and reject traversal and symlink components.

    Check the lexical path before resolving it: calling ``resolve()`` first would
    erase evidence that the user supplied a symlink. Symlink rejection is
    deliberate because evidence hashes should refer to the visible project file,
    not to a target that can be swapped behind that path.
    """
    root = project.resolve()
    candidate = Path(file).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    # Normalize '.' and '..' without following symlinks, then enforce containment.
    candidate = Path(os.path.abspath(candidate))
    if not candidate.is_relative_to(root):
        raise ValueError("File path escapes project root; copy an approved artifact into project first")

    cursor = root
    for part in candidate.relative_to(root).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Symlink paths are not accepted for evidence: " + str(cursor))

    path = candidate.resolve()
    if not path.is_relative_to(root):
        raise ValueError("File path escapes project root; copy an approved artifact into project first")
    if must_exist and not path.is_file():
        raise ValueError("File missing or not a regular file: " + str(path))
    return path


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@contextlib.contextmanager
def local_lock(path: Path):
    """Local filesystem O_EXCL lock. Stale locks require operator intervention."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(f"Project is locked ({path}); inspect before deleting a stale lock") from exc
    try:
        os.write(fd, f"pid={os.getpid()} at={now()}\n".encode())
        os.close(fd)
        yield
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        path.unlink(missing_ok=True)


def append_event(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now(), **event}, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def fail(exc: Exception) -> int:
    print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
    return 2
