from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
import csv
import hashlib
import json
import os

DEFAULT_IGNORES = {'.git', '.idea', '.vscode', '__pycache__', '.pytest_cache', 'node_modules'}

@dataclass(frozen=True)
class FileInfo:
    relpath: str
    size: int
    mtime_ns: int
    sha256: str | None = None

@dataclass(frozen=True)
class DiffEntry:
    relpath: str
    status: str
    left: FileInfo | None
    right: FileInfo | None
    renamed_from: str | None = None


def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def scan_tree(root: str | Path, *, hash_files: bool = False, ignores: Iterable[str] = DEFAULT_IGNORES) -> dict[str, FileInfo]:
    root = Path(root).expanduser().resolve()
    ignore_set = set(ignores)
    out: dict[str, FileInfo] = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ignore_set]
        base_path = Path(base)
        for name in files:
            p = base_path / name
            try:
                st = p.stat()
            except (FileNotFoundError, PermissionError, OSError):
                continue
            rel = p.relative_to(root).as_posix()
            sha = _hash_file(p) if hash_files else None
            out[rel] = FileInfo(rel, st.st_size, st.st_mtime_ns, sha)
    return out


def compare_trees(left: dict[str, FileInfo], right: dict[str, FileInfo], *, detect_renames: bool = True) -> list[DiffEntry]:
    entries: list[DiffEntry] = []
    left_only: dict[str, FileInfo] = {}
    right_only: dict[str, FileInfo] = {}

    for path in sorted(set(left) | set(right)):
        l = left.get(path)
        r = right.get(path)
        if l and r:
            same = (l.size == r.size and (l.sha256 == r.sha256 if l.sha256 and r.sha256 else l.mtime_ns == r.mtime_ns))
            entries.append(DiffEntry(path, 'unchanged' if same else 'modified', l, r))
        elif l:
            left_only[path] = l
        elif r:
            right_only[path] = r

    used_right: set[str] = set()
    if detect_renames:
        by_sig: dict[tuple[int, str], list[str]] = {}
        for p, info in right_only.items():
            if info.sha256:
                by_sig.setdefault((info.size, info.sha256), []).append(p)
        for p, info in sorted(left_only.items()):
            if info.sha256:
                candidates = [x for x in by_sig.get((info.size, info.sha256), []) if x not in used_right]
                if candidates:
                    target = candidates[0]
                    used_right.add(target)
                    entries.append(DiffEntry(target, 'renamed', info, right_only[target], renamed_from=p))
                else:
                    entries.append(DiffEntry(p, 'removed', info, None))
            else:
                entries.append(DiffEntry(p, 'removed', info, None))
    else:
        entries.extend(DiffEntry(p, 'removed', info, None) for p, info in sorted(left_only.items()))

    entries.extend(DiffEntry(p, 'added', None, info) for p, info in sorted(right_only.items()) if p not in used_right)
    return sorted(entries, key=lambda e: (e.status, e.relpath.lower()))


def summarize(entries: Iterable[DiffEntry]) -> dict[str, int]:
    summary = {k: 0 for k in ('added', 'removed', 'modified', 'renamed', 'unchanged')}
    for e in entries:
        summary[e.status] = summary.get(e.status, 0) + 1
    return summary


def export_json(entries: Iterable[DiffEntry], path: str | Path) -> None:
    payload = []
    for e in entries:
        d = asdict(e)
        payload.append(d)
    Path(path).write_text(json.dumps(payload, indent=2), encoding='utf-8')


def export_csv(entries: Iterable[DiffEntry], path: str | Path) -> None:
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['status', 'path', 'renamed_from', 'left_size', 'right_size'])
        for e in entries:
            writer.writerow([e.status, e.relpath, e.renamed_from or '', e.left.size if e.left else '', e.right.size if e.right else ''])