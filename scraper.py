from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime

CONFIG_FILE = "config.json"
DATA_FILE = "postliste.json"

BASE_URL = (
    "https://www.strand.kommune.no/tjenester/politikk-innsyn-og-medvirkning/"
    "postliste-dokumenter-og-vedtak/sok-i-post-dokumenter-og-saker/#/?page={page}&pageSize=100"
)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "mode": "incremental",
        "max_pages_incremental": 5,
        "max_pages_update": 200,
        "per_page": 50
    }

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return {d["dokumentID"]: d for d in json.load(f)}
    return {}

def safe_text(element, selector: str) -> str:
    node = element.query_selector(selector)
    return node.inner_text().strip() if node else ""

def hent_side(page_num: int, browser):
    url = BASE_URL.format(page=page_num)
    print(f"[INFO] Åpner side {page_num}: {url}")
    page = browser.new_page()
    try:
        page.goto(url, timeout=15000)
        page.wait_for_selector("article.bc-content-teaser--item", timeout=5000)
    except Exception as e:
        print(f"[WARN] Ingen oppføringer på side {page_num} ({e})")
        page.close()
        return []

    articles = page.query_selector_all("article.bc-content-teaser--item")
    dokumenter = []
    for art in articles:
        tittel = safe_text(art, ".bc-content-teaser-title-text")
        dato = safe_text(art, ".bc-content-teaser-meta-property--dato dd")
        dokid = safe_text(art, ".bc-content-teaser-meta-property--dokumentID dd")
        doktype = safe_text(art, ".bc-content-teaser-meta-property--dokumenttype dd")

        mottaker = ""
        if "Inngående" in doktype:
            mottaker = safe_text(art, ".bc-content-teaser-meta-property--avsender dd")
        elif "Utgående" in doktype:
            mottaker = safe_text(art, ".bc-content-teaser-meta-property--mottaker dd")

        link_elem = art.evaluate_handle("node => node.closest('a')")
        detalj_link = link_elem.get_attribute("href") if link_elem else ""

        filer = []
        if detalj_link:
            detail_page = browser.new_page()
            try:
                detail_page.goto(detalj_link, timeout=15000)
                file_links = detail_page.query_selector_all("a")
                for fl in file_links:
                    href = fl.get_attribute("href")
                    tekst = fl.inner_text()
                    if href and "/api/presentation/v2/nye-innsyn/filer" in href:
                        filer.append({
                            "tekst": tekst,
                            "url": "https://www.strand.kommune.no" + href
                        })
            except Exception as e:
                print(f"[WARN] Klarte ikke hente filer for '{tittel}': {e}")
            finally:
                detail_page.close()

        dokumenter.append({
            "tittel": tittel,
            "dato": dato,
            "dokumentID": dokid,
            "dokumenttype": doktype,
            "avsender_mottaker": mottaker,
            "side": page_num,
            "detalj_link": detalj_link,
            "filer": filer,
            "status": "Publisert" if filer else "Må bes om innsyn"
        })
    page.close()
    return dokumenter

def main():
    print("[INFO] Starter scraper…")
    config = load_config()
    mode = config.get("mode", "incremental")
    max_pages = config["max_pages_incremental"] if mode == "incremental" else config["max_pages_update"]
    per_page = config.get("per_page", 50)

    existing = load_existing()
    updated = dict(existing)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        for page_num in range(1, max_pages + 1):
            docs = hent_side(page_num, browser)
            if not docs:
                break
            for d in docs:
                if d["dokumentID"] not in updated:
                    print(f"[NEW] Ny oppføring: {d['dokumentID']} – {d['tittel']}")
                    updated[d["dokumentID"]] = d
                else:
                    # Oppdater hvis status eller filer har endret seg
                    old = updated[d["dokumentID"]]
                    if old["status"] != d["status"] or len(old.get("filer", [])) != len(d.get("filer", [])):
                        print(f"[UPDATE] Oppdatert oppføring: {d['dokumentID']} – {d['tittel']}")
                        updated[d["dokumentID"]] = d
            if mode == "incremental":
                # Stopp når vi ser en kjent ID
                if any(d["dokumentID"] in existing for d in docs):
                    print("[INFO] Stoppet – resten er gamle oppføringer.")
                    break
        browser.close()

    # lagre JSON
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(updated.values()), f, ensure_ascii=False, indent=2)
    print(f"[INFO] Lagret JSON med {len(updated)} dokumenter")

    # lag HTML (samme som før, men med perPage fra config)
    html = f"""<!doctype html>
<html lang="no">
<head>
<meta charset="utf-8">
<title>Postliste</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
.card {{ border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; }}
.status-publisert {{ color: green; font-weight: bold; }}
.status-innsyn {{ color: red; font-weight: bold; }}
</style>
</head>
<body>
<h1>Postliste – Strand kommune</h1>
<p>Oppdatert: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
<div id="container"></div>
<div id="pagination"></div>
<script>
const data = {json.dumps(list(updated.values()), ensure_ascii=False)};
let perPage = {per_page};
let currentPage = 1;

function renderPage(page) {{
  const start = (page-1)*perPage;
  const end = start+perPage;
  const items = data.slice(start,end);
  document.getElementById("container").innerHTML = items.map(d =>
    `<div class='card'>
      <h3>${{d.tittel}}</h3>
      <p>${{d.dato}} – ${{d.dokumentID}} – ${{d.dokumenttype}}</p>
      ${{d.avsender_mottaker ? `<p>Avsender/Mottaker: ${{d.avsender_mottaker}}</p>` : ""}}
      <p>Status: <span class='${{d.status==="Publisert"?"status-publisert":"status-innsyn"}}'>${{d.status}}</span></p>
      <p><a href='${{d.detalj_link}}' target='_blank'>Detaljer</a></p>
      ${{d.filer.length ? "<ul>" + d.filer.map(f => `<li><a href='${{f.url}}' target='_blank'>${{f.tekst}}</a></li>`).join("") + "</ul>" : "<p><a href='${{d.detalj_link}}' target='_blank'>Be om innsyn</a></p>"}}
    </div>`
  ).join("");
  document.getElementById("pagination").innerHTML =
    `<button onclick='prevPage()' ${{page===1?"disabled":""}}>Forrige</button>
     Side ${{page}} av ${{Math.ceil(data.length
