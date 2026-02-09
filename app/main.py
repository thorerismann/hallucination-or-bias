from dataclasses import asdict, is_dataclass
from pathlib import Path

from post_processing import create_final_webdata_dataset, prepare_results_frame
from html_parse import process_input_data, save_data
from prompting import score_folder
from settings import Settings


def extract_htmls(settings):
    all_data = process_input_data(settings.input_file)
    save_data(all_data, settings.webdata_dir)


def run_pipeline():
    settings = Settings()
    # extract_htmls(settings)
    # score_folder(settings)
    results_bias = prepare_results_frame(settings)
    # web_data = create_final_webdata_dataset(settings)
    print('hallo')
    results_bias.to_csv('bias_data_2.csv', index=False)
    # web_data.to_csv('web_data.csv', index=False)

run_pipeline()

