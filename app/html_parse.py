
import json
import pandas as pd
from dataclasses import dataclass, is_dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from urllib.request import urlopen, Request

import re
from pathlib import Path

from bs4 import BeautifulSoup


# ---------- Dataclass (schema enforcement) ----------

@dataclass
class RTSArticle:
    # Core content
    title: Optional[str]
    lead: Optional[str]
    body: Optional[str]

    # Structured (from JSON-LD)
    headline: Optional[str]
    alternative_headline: Optional[str]
    description: Optional[str]
    keywords: List[str]
    article_section: Optional[str]
    in_language: Optional[str]
    canonical_url: Optional[str]
    publisher_name: Optional[str]

    # Dates
    date_published: Optional[str]
    date_accessed: str

    # Other extracted blocks
    sources: List[str]
    credit: List[str]

# prepare data
def process_input_data(file_path):
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


# ---------- Fetch ----------

def fetch_rts_soup(url: str) -> BeautifulSoup:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "fr-CH,fr;q=0.9,en;q=0.8,de;q=0.7",
        },
    )

    with urlopen(req, timeout=15) as r:
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "text/html" not in ctype:
            raise ValueError(f"Not HTML: {ctype}")

        html = r.read().decode("utf-8", errors="ignore")

    soup = BeautifulSoup(html, "html.parser")
    if not soup.html or not soup.body:
        raise ValueError("Malformed or non-document HTML")

    return soup

def extract_jsonld_newsarticle(soup: BeautifulSoup) -> Dict[str, Any]:
    """Fail-soft: returns {} if not found or not parseable."""
    if not soup:
        return {}

    scripts = soup.select('script[type="application/ld+json"]')
    for sc in scripts:
        raw = sc.string
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        article = _pick_newsarticle(data)
        if isinstance(article, dict):
            # Heuristic: prefer objects that look like the one you pasted
            if article.get("@type") in ("NewsArticle", "Article") or "headline" in article or "datePublished" in article:
                return article

    return {}

def _pick_newsarticle(obj: Any) -> Optional[Dict[str, Any]]:
    """
    Return the JSON-LD object whose @type is NewsArticle or Article.
    Otherwise return None (fail-fast).
    """

    # Case 1: single dict
    if isinstance(obj, dict):
        if obj.get("@type") in ("NewsArticle", "Article"):
            return obj
        return None

    # Case 2: list of dicts
    if isinstance(obj, list):
        for it in obj:
            if isinstance(it, dict) and it.get("@type") in ("NewsArticle", "Article"):
                return it
        return None
    # Anything else → fail
    return None


# ---------- Safe extractor helper (fail-soft) ----------

def safe_text(node, selector, default=None, many=False):
    if not node:
        return default

    if many:
        els = node.select(selector)
        return [el.get_text(" ", strip=True) for el in els] if els else default

    el = node.select_one(selector)
    return el.get_text(" ", strip=True) if el else default

def safe_strip(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s2 = s.strip()
    return s2 if s2 else None


# ---------- Field extractors ----------

def extract_description(soup):
    meta = soup.select_one('meta[name="dcterms.description"]')
    return meta.get("content") if meta else None


def extract_title(soup) -> Optional[str]:
    return soup.title.string.strip() if soup.title and soup.title.string else None


def extract_lead(soup) -> Optional[str]:
    return safe_text(
        soup,
        "div.article-part.article-lead",
        default=None,
    )


def extract_body(body) -> Optional[str]:
    if not body:
        return None

    parts: List[str] = []
    for el in body.select("p, h2, h3"):
        classes = el.get("class", []) or []
        if "sources" in classes or "credit" in classes:
            break
        if classes:
            continue

        txt = el.get_text(" ", strip=True)
        if txt:
            parts.append(txt)

    return "\n\n".join(parts) if parts else None


def extract_sources(body) -> List[str]:
    return safe_text(
        body,
        "p.sources",
        default=[],
        many=True,
    )


def extract_credits(body) -> List[str]:
    return safe_text(
        body,
        "p.credit",
        default=[],
        many=True,
    )


def extract_date_published(soup) -> Optional[str]:
    time_tag = soup.find("time", datetime=True)
    if not time_tag:
        return None

    raw = time_tag["datetime"]
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")) \
                       .strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return raw



# ---------- JSON extractors ----------

def extract_keywords_from_jsonld(j: Dict[str, Any]) -> List[str]:
    kw = j.get("keywords")
    if isinstance(kw, list):
        return [k for k in (safe_strip(str(x)) for x in kw) if k]
    if isinstance(kw, str):
        # sometimes comma-separated
        parts = [p.strip() for p in kw.split(",")]
        return [p for p in parts if p]
    return []


def extract_publisher_name(j: Dict[str, Any]) -> Optional[str]:
    pub = j.get("publisher")
    if isinstance(pub, dict):
        return safe_strip(pub.get("name"))
    return None

def extract_canonical_url(j: Dict[str, Any]) -> Optional[str]:
    canonical_url = j.get("mainEntityOfPage")
    if canonical_url:
        return safe_strip(canonical_url)
    return None

def extract_alt_headline(j: Dict[str, Any]) -> Optional[str]:
    alt_headline = j.get("alternativeHeadline")
    if alt_headline:
        return safe_strip(alt_headline)
    return None

def extract_headline(j: Dict[str, Any]) -> Optional[str]:
    headline = j.get("headline")
    if headline:
        return safe_strip(headline)
    return None

def extract_article_section(j: Dict[str, Any]) -> Optional[str]:
    article_section = j.get("articleSection")
    if article_section:
        return safe_strip(article_section)
    return None

def extract_language(j: Dict[str, Any]) -> Optional[str]:
    lang = j.get("inLanguage")
    if lang:
        return safe_strip(lang)
    return None

# ---------- Orchestrator ----------

def parse_html(url: str) -> RTSArticle:
    soup = fetch_rts_soup(url)
    jsonld = extract_jsonld_newsarticle(soup)
    return RTSArticle(
        title=extract_title(soup),
        lead=extract_lead(soup),
        body=extract_body(soup.body),
        sources=extract_sources(soup.body),
        credit=extract_credits(soup.body),
        date_published=extract_date_published(soup),
        date_accessed=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        keywords=extract_keywords_from_jsonld(jsonld),
        publisher_name=extract_publisher_name(jsonld),
        in_language=extract_language(jsonld),
        article_section=extract_article_section(jsonld),
        headline=extract_headline(jsonld),
        alternative_headline=extract_alt_headline(jsonld),
        canonical_url=extract_canonical_url(jsonld),
        description=extract_description(soup)


    )

# save the data

def make_filename(article):
    # 1) Try RTS numeric ID from URL
    url = article.get("canonical_url") or article.get("url")
    if isinstance(url, str):
        m = re.search(r"-(\d+)\.html$", url)
        if m:
            return f"{m.group(1)}.json"

    # 2) Fallback: short title slug
    title = article.get("title") or article.get("headline") or "article"
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", title.lower()).strip("_")
    return f"{slug[:30]}.json"


def save_data(articles, directory):
    for article in articles:
        fname = make_filename(article)
        save_path = directory / fname
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)