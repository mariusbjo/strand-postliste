import os
import json
from datetime import datetime
from urllib.parse import urljoin, quote
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.strand.kommune.no"
POSTLISTE_URL = "https://www.strand.kommune.no/tjenester/politikk-innsyn-og-medvirkning/postliste-dokumenter-og-vedtak/sok-i-post-dokumenter-og-saker/"
OUTPUT_DIR = "."
POSTMOTTAK_EMAIL = "postmottak@strand.kommune.no"

def hent_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PostlisteScraper/1.0)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def parse_postliste(html):
    soup = BeautifulSoup(html, "html.parser")
    dokumenter = []
    rows = soup.select("table.searchResult tr") or soup.select("div.search-result")
    for rad in rows:
        celler = rad.find_all("td")
        if not celler:
            continue
        dato = celler[0].get_text(strip=True) if len(celler) > 0 else ""
        tittel_elem = celler[1] if len(celler) > 1 else None
        tittel = tittel_elem.get_text(strip=True) if tittel_elem else ""
        pdf_link, detalj_link = None, None
        if tittel_elem:
            link_tag = tittel_elem.find("a")
            if link_tag and link_tag.get("href"):
                href = link_tag["href"]
                if href.lower().endswith(".pdf"):
                    pdf_link = urljoin(BASE_URL, href)
                else:
                    detalj_link = urljoin(BASE_URL, href)
        avsender = celler[2].get_text(strip=True) if len(celler) > 2 else ""
        mottaker = celler[3].get_text(strip=True) if len(celler) > 3 else ""
        saksnr = celler[4].get_text(strip=True) if len(celler) > 4 else ""
        krever_innsyn = False
        if not pdf_link or "innsyn" in tittel.lower():
            krever_innsyn = True
        dokumenter.append({
            "dato": dato,
            "tittel": tittel,
            "avsender": avsender,
            "mottaker": mottaker,
            "saksnr": saksnr,
            "pdf_link": pdf_link,
            "detalj_link": detalj_link,
            "krever_innsyn": krever_innsyn
        })
    print(f"Fant {len(dokumenter)} dokumenter i postlisten.")
    return dokumenter

def lag_mailto_innsyn(dok):
    emne = f"Innsynsbegjæring – {dok.get('tittel') or 'Dokument'} ({dok.get('dato')})"
    body = f"Hei Strand kommune,\n\nJeg ber om innsyn i dokumentet:\n{dok}\n\nVennlig hilsen\nNavn"
    return f"mailto:{POSTMOTTAK_EMAIL}?subject={quote(emne)}&body={quote(body)}"

def render_html(dokumenter):
    if not dokumenter:
        content = "<p>Ingen dokumenter funnet i postlisten.</p>"
    else:
        cards = []
        for dok in dokumenter:
            title = dok.get("tittel") or "Uten tittel"
            meta = f"Dato: {dok.get('dato','')} · Saksnr: {dok.get('saksnr','')}"
            actions = []
            if dok.get("pdf_link"):
                actions.append(f"<a href='{dok['pdf_link']}' target='_blank'>Åpne PDF</a>")
            elif dok.get("detalj_link"):
                actions.append(f"<a href='{dok['detalj_link']}' target='_blank'>Detaljer</a>")
            if dok.get("krever_innsyn"):
                actions.append(f"<a href='{lag_mailto_innsyn(dok)}'>Be om innsyn</a>")
            card = (
                "<section class='card'>"
                f"<h3>{title}</h3>"
                f"<div class='meta'>{meta}</div>"
                f"<div class='actions'>{' '.join(actions)}</div>"
                "</section>"
            )
            cards.append(card)
        content = "\n".join(cards)
    html = f"""<!doctype html>
<html lang="no">
<head>
  <meta charset="utf-8">
  <title>Strand kommune – uoffisiell postliste</title>
</head>
<body>
  <h1>Postliste – Strand kommune (uoffisiell speiling)</h1>
  <p>Oppdatert: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
  {content}
</body>
</html>
"""
    out_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Skrev index.html til {out_path}")

def main():
    try:
        html = hent_html(POSTLISTE_URL)
    except Exception as e:
        print(f"Feil ved henting: {e}")
        return
    dokumenter = parse_postliste(html)
    render_html(dokumenter)
    json_path = os.path.join(OUTPUT_DIR, "postliste.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dokumenter, f, ensure_ascii=False, indent=2)
    print(f"Lagret JSON til {json_path}")

if __name__ == "__main__":
    main()
