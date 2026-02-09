from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional

import pandas as pd
_WS_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")  # cheap HTML tag strip (if any leaked in)

def calculate_overall_bias(df):
    df['overall_bias'] = df[["subject_bias", "framing_bias", "treatment_bias", "guests_bias"]].mean(axis=1)
    return df

def prepare_results_frame(settings):
    rows = []
    for i in range(1,settings.runs+1):
        for model in settings.models:
            this_model_dir = settings.final_dir / model.replace(":", "_") / str(i)
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
                    "run": i,
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    df = calculate_overall_bias(df)
    return df



def _clean_text(x: Any) -> Optional[str]:
    """Normalize whitespace; strip; remove simple HTML tags; keep None as None."""
    if x is None:
        return None
    if not isinstance(x, str):
        x = str(x)
    x = _TAG_RE.sub(" ", x)
    x = _WS_RE.sub(" ", x).strip()
    return x or None

def _ensure_list(x: Any) -> List[str]:
    """Force list[str] with cleaned strings; None -> []"""
    if x is None:
        return []
    if isinstance(x, list):
        out = []
        for v in x:
            cv = _clean_text(v)
            if cv:
                out.append(cv)
        return out
    cv = _clean_text(x)
    return [cv] if cv else []



def _word_count(text: Optional[str]) -> int:
    if not text:
        return 0
    # simple whitespace tokenization (good enough for descriptive counts)
    return len(text.split())

def _char_count(text: Optional[str]) -> int:
    return len(text) if text else 0

def _to_datetime(series: pd.Series) -> pd.Series:
    # your example uses "YYYY-MM-DD HH:MM:SS"
    return pd.to_datetime(series, errors="coerce", utc=False)


def prepare_raw_frame(webdata_dir: Path) -> pd.DataFrame:
    records = []

    for p in sorted(Path(webdata_dir).glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error reading {p}: {e}")
            continue

        data["article_id"] = p.stem
        data["file_path"] = str(p)
        records.append(data)

    df = pd.DataFrame.from_records(records)

    # optional: select/rename columns after
    keep = [
        "article_id", "file_path",
        "title", "headline", "alternative_headline",
        "lead", "body", "description",
        "canonical_url", "publisher_name",
        "article_section", "in_language",
        "date_published", "date_accessed",
        "keywords", "sources", "credit",
    ]
    return df[[c for c in keep if c in df.columns]]



def clean_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean / normalize text and list fields; parse dates; normalize URL.
    """
    df = df.copy()

    # Clean text fields
    text_cols = [
        "title", "headline", "alternative_headline",
        "lead", "body", "description",
        "canonical_url", "publisher_name", "article_section", "in_language",
    ]
    for c in text_cols:
        if c in df.columns:
            df[c] = df[c].map(_clean_text)

    # Normalize list fields
    for c in ["keywords", "sources", "credit"]:
        if c in df.columns:
            df[c] = df[c].map(_ensure_list)

    # Parse datetimes
    for c in ["date_published", "date_accessed"]:
        if c in df.columns:
            df[c] = _to_datetime(df[c])

    # Convenience: domain
    if "canonical_url" in df.columns:
        df["canonical_domain"] = df["canonical_url"].map(
            lambda u: None if not u else (u.split("/")[2] if "://" in u else None)
        )

    return df


def create_wordcounts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create word/char counts for title/lead/body and a total.
    """
    df = df.copy()

    for field in ["title", "lead", "body"]:
        if field in df.columns:
            df[f"{field}_words"] = df[field].map(_word_count).astype(int)
            df[f"{field}_chars"] = df[field].map(_char_count).astype(int)

    df["text_words_total"] = (
        df.get("title_words", 0) + df.get("lead_words", 0) + df.get("body_words", 0)
    ).astype(int)

    return df


def create_final_webdata_dataset(settings) -> pd.DataFrame:
    """
    Build a cleaned dataset from settings.webdata_dir only.
    No merge with model outputs.
    """
    webdata_dir = Path(settings.webdata_dir)
    df = prepare_raw_frame(webdata_dir)
    df = clean_fields(df)
    df = create_wordcounts(df)

    # Optional: stable column order
    preferred = [
        "article_id",
        "canonical_url", "canonical_domain",
        "publisher_name", "article_section", "in_language",
        "date_published", "date_accessed",
        "headline", "title", "alternative_headline",
        "lead", "description",
        "title_words", "lead_words", "body_words", "text_words_total",
        "title_chars", "lead_chars", "body_chars",
        "keywords", "sources", "credit",
        "file_path",
    ]
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    df = df[cols]

    return df

