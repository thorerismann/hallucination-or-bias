import json
from pathlib import Path
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODELS = ["gemma3:4b", "llama3.2:latest", "qwen3:4b", "gemma2:latest", "phi3:mini", "qwen2.5:3b-instruct"]

PROMPT_TEMPLATE = Path(r"app/prompt.md").read_text(encoding="utf-8")  # contains {{ARTICLE_TEXT}}

ARTICLES_DIR = Path(r"C:\Users\erismanng\pbias2\hallucination-or-bias\app\webdata")
OUTPUT_DIR = Path(r"C:\Users\erismanng\pbias2\hallucination-or-bias\app\final")  # folder to save model outputs

def call_ollama(model: str, prompt: str, timeout: int = 180) -> str:
    r = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9, "num_predict": 400},
        },
        timeout=timeout,
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


def parse_json_from_model(text: str) -> dict:
    # strict: expect JSON only (your prompt demands it)
    # fail-soft: raise if not JSON so you can see breakages immediately
    clean = strip_markdown_json(text)
    data = json.loads(clean)
    return data


def score_one_article(article_path: Path, model: str) -> dict:
    article = json.loads(article_path.read_text(encoding="utf-8"))
    body = article["body"]  # you said this key is valid

    prompt = PROMPT_TEMPLATE.replace("{{ARTICLE_TEXT}}", body)

    raw = call_ollama(model, prompt)
    results = parse_json_from_model(raw)
    return results


def save_model_results(results: dict, output_file: Path) -> None:
    output_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def score_folder(folder: Path, runs: int):
    i = 0
    for model in MODELS:
        for i in range(1, runs + 1):
            print(f"Run {i} for model {model}")
            output_folder = OUTPUT_DIR / model.replace(":", "_") / str(i)
            output_folder.mkdir(parents=True, exist_ok=True)
            for p in sorted(folder.glob("*.json")):
                print(f"Processing article: {p.name}")
                try:
                    file_name = output_folder / f"{p.stem}.json"
                    if file_name.exists():
                        print(f"Skipping existing file: {file_name}")
                        continue
                    score = score_one_article(p, model)
                    save_model_results(score, file_name)
                except Exception as e:
                    print(f"Error processing {p}: {e}")
