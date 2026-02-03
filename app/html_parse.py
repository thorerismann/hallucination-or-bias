from datetime import datetime
from bs4 import BeautifulSoup

def extract_rts_article_from_body(body) -> dict:
    # 1) Main text (include h2 as normal text)
    parts = []
    for el in body.select("p, h2, h3"):
        # skip metadata paragraphs from main text
        classes = el.get("class", []) or []
        if "sources" in classes or "credit" in classes:
            break
        txt = el.get_text(" ", strip=True)
        if txt:
            parts.append(txt)

    main_text = "\n\n".join(parts)
    print(main_text)
    return main_text



def extract_source(body):
    # 2) Sources + credits
    sources = [p.get_text(" ", strip=True) for p in body.select("p.sources")]
    print(sources)
    return sources

def extract_credits(body):
    credits = [p.get_text(" ", strip=True) for p in body.select("p.credit")]
    print(credits)
    return credits

def parse_html(html)-> dict:
    mydict = {}
    soup = BeautifulSoup(html, "html.parser")
    mydict['title'] = soup.title.string
    mydict['body'] = extract_rts_article_from_body(soup.body)
    mydict['source']= extract_source(soup.body)
    mydict['credit'] = extract_credits(soup.body)
    mydict['date_accessed'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    mydict['date_published'] = '???'
    return mydict
