from __future__ import annotations
from pathlib import Path

def find_project_root(start: Path | None = None) -> Path:
    """
    Find the project root defined as the directory that contains the 'app/' folder.
    Works no matter what the current working directory is.
    """
    p = (start or Path.cwd()).resolve()
    for parent in [p, *p.parents]:
        if (parent / "app").is_dir():
            return parent
    raise RuntimeError(f"Could not find project root (no 'app/' dir) from {p}")

def project_root_from_file(file: str) -> Path:
    """
    Stronger anchor than cwd: starts from the file location.
    Use this inside app/settings.py to avoid cwd issues entirely.
    """
    return find_project_root(Path(file).resolve().parent)
