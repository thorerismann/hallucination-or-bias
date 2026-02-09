import json
from pathlib import Path
import requests
import re
from typing import Any

_LEADING_ZERO_NUM = re.compile(r'(:\s*)(-?)00(?=[\d.])')

def parse_json_with_number_fix(raw: str) -> str:
    raw = _LEADING_ZERO_NUM.sub(r"\1\20", raw)  # ": -00.2" -> ": -0.2"
    return raw

def call_ollama(model: str, prompt: str, settings) -> str:
    r = requests.post(
        settings.ollama_url,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": settings.ollama_options,
        },
        timeout=settings.timeout,
    )
    r.raise_for_status()
    return r.json().get("response", "")


def strip_markdown_json(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        # remove opening fence (``` or ```json)
        text = text.split("\n", 1)[1]

    if text.endswith("```"):
        # remove closing fence
        text = text.rsplit("\n", 1)[0]

    return text.strip()


def parse_json_from_model(text: str) -> dict[str, Any]:
    raw = strip_markdown_json(text)

    # 1) normal parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e1:
        err1 = e1

    # 2) number-fix parse
    try:
        print('Trying to fix leading 0s...')
        fixed = parse_json_with_number_fix(raw)
        return json.loads(fixed)
    except json.JSONDecodeError as e2:
        err2 = e2

    # 3) truncation/structure repair (last resort)
    # Optional: only attempt repair if it looks like JSON at all.
    print("trying to fix truncation issue...")
    if "{" not in raw:
        raise ValueError("Model output doesn't contain a JSON object.") from err2

    repaired = raw.strip()

    # If the last value is an unterminated string, close it (heuristic)
    # Note: this counts all quotes, including escaped quotes. Good enough for many cases,
    # but can be improved later by counting only unescaped quotes.
    if repaired.count('"') % 2 == 1:
        repaired += '"'

    # Ensure object closes
    if not repaired.endswith("}"):
        repaired += "\n}"

    try:
        return json.loads(repaired)
    except json.JSONDecodeError as e3:
        # Raise with context so you can see what happened
        msg = (
            "Failed to parse model output as JSON after: normal parse, number-fix, and repair.\n"
            f"normal error: {err1}\n"
            f"number-fix error: {err2}\n"
            f"repair error: {e3}\n"
        )
        raise ValueError(msg) from e3

def load_article_body(article_path: Path) -> dict:
    article = json.loads(article_path.read_text(encoding="utf-8"))
    body = article["body"]
    return body

def score_one_article(article_path: Path, model: str, settings) -> dict[str, Any]:
    body = load_article_body(article_path)
    prompt = settings.prompt_template.replace("{{ARTICLE_TEXT}}", body)

    try:
        raw = call_ollama(model, prompt, settings)
    except Exception as e:
        return {
            "_error": "call_ollama_failed",
            "model": model,
            "article": article_path.name,
            "exception": repr(e),
        }

    try:
        results = parse_json_from_model(raw)
        return results
    except Exception as e:
        return {
            "_error": "json_parse_failed",
            "model": model,
            "article": article_path.name,
            "exception": repr(e),
            "raw_model_output": raw,  # keep this if disk space is ok; otherwise truncate
        }



def save_model_results(results: dict, output_file: Path) -> None:
    output_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def score_folder(settings):
    i = 0
    for model in settings.models:
        print(f"<------NEW MODEL: {model}------>")
        for i in range(1, settings.runs + 1):
            print(f"<------------------- Run {i} for model {model} ---------------->")
            output_folder = settings.final_dir / model.replace(":", "_") / str(i)
            output_folder.mkdir(parents=True, exist_ok=True)
            for p in sorted(settings.webdata_dir.glob("*.json")):
                print(f"Processing article: {p.name}")
                file_name = output_folder / f"{p.stem}.json"
                if file_name.exists():
                    continue
                score = score_one_article(p, model, settings)
                save_model_results(score, file_name)

