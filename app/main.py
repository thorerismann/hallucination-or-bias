from dataclasses import asdict, is_dataclass
from pathlib import Path
from html_parse import parse_html, save_data
from prompting import score_folder
from setup import INPUT_PATH, OUTPUT_PATH, check_for_inputs

RUNS = 5

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

def extract_htmls():
    input_files = check_for_inputs()
    if len(input_files) == 0:
        print('No valid input file found. Put a list of valid RTS urls in a CSV file.')
        return
    for input_file in input_files:
        all_data = process_csv(input_file)
        save_data(all_data)




# extract_htmls()
score_folder(Path(r'app\webdata'), RUNS)
