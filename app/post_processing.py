from pathlib import Path
import json
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

MODEL_DIR = Path(r"C:\Users\erismanng\pbias2\hallucination-or-bias\app\final")
models = ["gemma3:4b", "llama3.2:latest", "gemma2:latest", "phi3:mini", "qwen2.5:3b-instruct"]


def calculate_overall_bias(df):
    df['overall_bias'] = df[["subject_bias", "framing_bias", "treatment_bias", "guests_bias"]].mean(axis=1)
    return df

def prepare_full_frame():
    rows = []
    for model in models:
        this_model_dir = MODEL_DIR / model.replace(":", "_")
        for p in this_model_dir.glob("*.json"):
            print(p)
            data = json.loads(p.read_text(encoding="utf-8"))
            print(data)

            row = {
                "model": model,
                "article_id": p.stem,          # from filename
                "subject_bias": data.get("subject_bias"),
                "framing_bias": data.get("framing_bias"),
                "treatment_bias": data.get("treatment_bias"),
                "guests_bias": data.get("guests_bias"),
                "confidence": data.get("confidence"),
                "comment": data.get("comment"),
            }

            rows.append(row)

    df = pd.DataFrame(rows)
    df = calculate_overall_bias(df)
    return df



def make_scatter_chart(df):
    sns.scatterplot(data=df, x="article_id", y="overall_bias", hue="model")
    plt.show()




df = prepare_full_frame()
make_chart(df)
