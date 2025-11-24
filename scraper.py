import os
import re
import json
from datetime import datetime
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup

# Konfigurasjon
BASE_URL = "https://www.strand.kommune.no"
POSTLISTE_URL = "https://www.strand.kommune.no/tjenester/politikk-innsyn-og-medvirkning/postliste-dokumenter-og-vedtak/sok-i-post-dokumenter-og-saker/"

OUTPUT_DIR = "."
PDF_DIR = os.path.join(OUTPUT_DIR, "pdf_dokumenter")
TEMPLATES_DIR = os.path.join(OUTPUT_DIR, "templates")
ASSETS_DIR = os.path.join(OUTPUT_DIR, "assets")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

POSTMOTTAK_EMAIL = "postmottak@strand.kommune.no"

# ------------------- Hjelpefunksjoner -------------------

def hent_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PostlisteScraper/1.0)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def er_innsynsoppforing(celle_text: str) -> bool:
    txt = celle_text.lower()
    hints = ["innsyn", "ikke publisert", "ikke offentlig", "begrenset", "unntatt offentlighet"]
    return any(h in txt for h in hints)

def parse_postliste(html):
    """
    Parser HTML fra Strand kommunes postliste (ACOS).
    Returnerer en liste med dokumenter.
    """
    soup = BeautifulSoup(html, "html.parser")
    dokumenter = []

    # ACOS bruker ofte <table class="searchResult"> eller <div class="search-result">
    rows = soup.select("table.searchResult tr") or soup.select("div.search-result")

    for rad in rows:
        celler = rad.find_all("td")
        if not celler:
            continue

        # Typisk struktur: [Dato, Tittel, Avsender, Mottaker, Saksnr]
        dato = celler[0].get_text(strip=True) if len(celler) > 0 else ""
        tittel_elem = celler[1] if len(celler) > 1 else None
        tittel = tittel_elem.get_text(strip=True) if tittel_elem else ""

        # Finn lenke til PDF eller detaljside
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

        # Innsynsoppføring hvis ingen PDF eller teksten inneholder "innsyn"
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

def last_ned_pdf(url, filnavn):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; PostlisteScraper/1.0)"}
        r = requests.get(url, headers=headers, timeout=60)
        r.raise_for_status()
        path = os.path.join(PDF_DIR, filnavn)
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    except Exception as e:
        print(f"Feil ved nedlasting av {url}: {e}")
        return None

def lag_mailto_innsyn(dok):
    emne = f"Innsynsbegjæring – {dok.get('tittel') or 'Dokument'} ({dok.get('dato')})"
    body_lines = [
        "Hei Strand kommune,",
        "",
        "Jeg ber om innsyn i følgende dokument fra postlisten:",
        f"- Tittel: {dok.get('tittel')}",
        f"- Dato: {dok.get('dato')}",
        f"- Saksnummer: {dok.get('saksnr')}",
        f"- Avsender: {dok.get('avsender')}",
        f"- Mottaker: {dok.get('mottaker')}",
        "",
        "Hvis dokumentet er helt eller delvis unntatt offentlighet, ber jeg om en begrunnelse med hjemmel samt vurdering av meroffentlighet.",
        "",
        "Vennlig hilsen",
        "Navn",
    ]
    body = "\n".join(body_lines)
    return f"mailto:{POSTMOTTAK_EMAIL}?subject={quote(emne)}&body={quote(body)}"

# ------------------- HTML-rendering -------------------

def render_html(dokumenter):
    """
    Lager en enkel index.html med dokumentene.
    Hvis listen er tom, vises en melding.
    """
    # Bygg innhold
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

    # Minimal HTML-mal
    html = f"""<!doctype html>
<html lang="no">
<head>
  <meta charset="utf-8">
  <title>Strand kommune – uoffisiell postliste</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: sans-serif; margin: 2rem; background: #fafafa; }}
    .card {{ background: #fff; padding: 1rem; margin-bottom: 1rem; border: 1px solid #ddd; }}
    .meta {{ color: #555; font-size: 0.9em; margin-bottom: 0.5rem; }}
    .actions a {{ margin-right: 1rem; }}
  </style>
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

