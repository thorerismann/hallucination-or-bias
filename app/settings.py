from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Settings:
    # directories are relative to the project root (folder containing main.py)
    input_file: Path = Path("app/input_files/more_rts_links.csv")
    webdata_dir: Path = Path("app/webdata")
    final_dir: Path = Path("app/final")


    runs: int = 5
    timeout: int = 240
    ollama_url: str = "http://127.0.0.1:11434/api/generate"
    models: List[str] = None  # type: ignore[assignment]

    prompt_template: Path = Path("app/prompt.md")

    def __post_init__(self) -> None:
        if self.models is None:
            object.__setattr__(
                self,
                "models",
                ["llama3.2:latest", "gemma2:latest", "phi3:mini", "qwen2.5:3b-instruct", "gemma3:4b"],
            )
