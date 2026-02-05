from dataclasses import asdict, is_dataclass
from pathlib import Path
from html_parse import parse_html, save_data
from prompting import score_folder
from setup import load_settings


def process_csv(file_path):
    with open(file_path, 'r') as f:
        urls = f.readlines()
    articles = []
    for url in urls:
        # check them
        # then call
        try:
            url = url.strip()
            if not url.startswith("http"):
                print(f"Skipping invalid URL: {url}")
                continue
            data = parse_html(url)
            if is_dataclass(data):
                data = asdict(data)
            articles.append(data)
        except Exception as e:
            print(f"Error processing {url}: {e}")
    return articles

def extract_htmls(settings: dict):
    all_data = process_csv(settings['INPUT_FILE'])
    save_data(all_data)


settings = load_settings(Path.cwd() / "app")

extract_htmls(settings)
score_folder(Path(r'app\webdata'), settings)
