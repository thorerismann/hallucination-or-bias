"""All pipeline functions receive a `Settings` instance.
No function should assume a dict-like interface.
Configuration values are accessed via attributes or properties:
    settings.webdata_dir
    settings.models
    settings.ollama_options
    settings.prompt_template
"""


from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any

from app.paths import project_root_from_file

ModelOptions = Dict[str, Any]

@dataclass(frozen=True)
class Settings:
    # Stable anchor: directory containing `app/`
    root: Path = field(default_factory=lambda: project_root_from_file(__file__))

    # ---- runtime params ----
    runs: int = 6
    timeout: int = 200
    ollama_url: str = "http://127.0.0.1:11434/api/generate"

    models: List[str] = field(default_factory=lambda: [
        "llama3.2:latest",
        "gemma2:latest",
        "phi3:mini",
        "qwen2.5:3b-instruct",
        "gemma3:4b",
    ])

    # Global Ollama options
    ollama_options: ModelOptions = field(default_factory=lambda: {
        "temperature": 0.8,
        "num_predict": 250,
        "num_ctx": 2048,
    })

    # ---- resolved paths (absolute) ----
    @property
    def input_file(self) -> Path:
        return self.root / "app" / "input_files" / "some_rts_links.csv"

    @property
    def webdata_dir(self) -> Path:
        return self.root / "app" / "webdata"

    @property
    def final_dir(self) -> Path:
        return self.root / "app" / "final"

    @property
    def prompt_template_path(self) -> Path:
        return self.root / "app" / "prompt.md"

    # ---- derived content ----
    @property
    def prompt_template(self) -> str:
        return self.prompt_template_path.read_text(encoding="utf-8")

    def __post_init__(self) -> None:
        # Hard fail early if structure is wrong
        if not (self.root / "app").is_dir():
            raise RuntimeError(f"Invalid project root: {self.root}")
