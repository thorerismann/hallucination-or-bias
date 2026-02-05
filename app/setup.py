# app/load_settings.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from settings import Settings


def project_root(anchor_file: str | Path) -> Path:
    """
    anchor_file: typically __file__ from main.py
    Returns the directory that contains main.py.
    """
    return Path(anchor_file).resolve().parent


def load_settings(anchor_file: str | Path) -> Dict[str, Any]:
    """
    Returns a dict with fully-resolved Paths and the loaded prompt text.
    Works on Windows + Linux.
    """
    root = project_root(anchor_file)
    s = Settings()

    # resolve directories/files relative to root
    input_dir = (root / s.input_file).resolve()
    webdata_dir = (root / s.webdata_dir).resolve()
    final_dir = (root / s.final_dir).resolve()
    prompt_path = (root / s.prompt_template).resolve()

    # ensure dirs exist
    webdata_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    prompt_text = prompt_path.read_text(encoding="utf-8")

    return {
        "PROJECT_ROOT": root,
        "INPUT_FILE": input_dir,
        "WEB_DATA_DIR": webdata_dir,
        "OUTPUT_DIR": final_dir,
        "RUNS": int(s.runs),
        "OLLAMA_URL": str(s.ollama_url),
        "MODELS": list(s.models),
        "PROMPT_TEMPLATE_PATH": prompt_path,
        "PROMPT_TEMPLATE": prompt_text,
        "TIMEOUT": s.timeout
    }
