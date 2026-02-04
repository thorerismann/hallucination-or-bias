from pathlib import Path

INPUT_PATH = Path(r"C:\Users\erismanng\pbias2\hallucination-or-bias\app\input_files")
OUTPUT_PATH = Path(r"C:\Users\erismanng\pbias2\hallucination-or-bias\app\webdata")

def check_input_output_paths():
    if not INPUT_PATH.exists():
        INPUT_PATH.mkdir(parents=True)
    if not OUTPUT_PATH.exists():
        OUTPUT_PATH.mkdir(parents=True)

def check_for_inputs():
    check_input_output_paths
    files = list(INPUT_PATH.iterdir())
    if len(files) == 0:
        print(f"No input files found in {INPUT_PATH}. Please add urls in csv format to process.")
        return None

    return files

def check_urls():
    # figure out how to check the urls for each file and give a warning if something is clearly wrong
    # hard to know until its processed exactly, but obvious file not right shit should be caught
    pass