from playwright.sync_api import sync_playwright
import json
import os
from datetime import datetime

OUTPUT_DIR = "."
BASE_URL = (
    "https://www.strand.kommune.no/tjenester/politikk-innsyn-og-medvirkning/"
    "postliste-dokumenter-og-vedtak/sok-i-post-dokumenter-og-saker/#/?page={page}&pageSize=100"
)

def safe_text(element, selector: str) -> str:
    node = element.query_selector(selector)
    return node.inner_text().strip() if node else ""

def hent_side(page_num: int, browser):
    url = BASE_URL.format(page=page_num)
    page = browser.new_page()
    page.goto(url, timeout=60000)
    try:
        page.wait_for_selector("article.bc-content-teaser--item", timeout=15000)
    except:
        print(f"[Side {page_num}] Ingen oppføringer funnet.")
        page.close()
        return []

    articles = page.query_selector_all("article.bc-content-teaser--item")
    dokumenter = []
    for art in articles:
        tittel = safe_text(art, ".bc-content-teaser-title-text")
        dato = safe_text(art, ".bc-content-teaser-meta-property--dato dd")
        dokid = safe_text(art, ".bc-content-teaser-meta-property--dokumentID dd")
        mottaker = safe_text(art, ".bc-content-teaser-meta-property--mottaker dd")

        # Hent detaljlenke fra <a> rundt artikkelen
        link_elem = art.evaluate_handle("node => node.closest('a')")
        detalj_link = ""
        if link_elem:
            detalj_link = link_elem.get_attribute("href") or ""

        dokumenter.append({
            "tittel": tittel,
            "dato": dato,
            "dokumentID": dokid,
            "mottaker": mottaker,
            "side": page_num,
            "detalj_link": detalj_link
        })
    page.close()
    print(f"[Side {page_num}] Fant {len(dokumenter)} dokumenter.")
    return dokumenter

def main():
    alle_dokumenter = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for page_num in range(1, 101):  # opptil 100 sider
            docs = hent_side(page_num, browser)
            if not docs:
                print(f"[Side {page_num}] Stopper – ingen flere dokumenter.")
                break
            alle_dokumenter.extend(docs)
            print(f"Totalt hittil: {len(alle_dokumenter)} dokumenter.")
        browser.close()

    # lagre JSON
    json_path = os.path.join(OUTPUT_DIR, "postliste.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(alle_dokumenter, f, ensure_ascii=False, indent=2)
    print(f"✅ Lagret JSON med {len(alle_dokumenter)} dokumenter til {json_path}")

    # lag HTML med paginering
    html = f"""<!doctype html>
<html lang="no">
<head>
<meta charset="utf-8">
<title>Postliste</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
.card {{ border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; }}
</style>
</head>
<body>
<h1>Postliste – Strand kommune</h1>
<p>Oppdatert: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
<div id="container"></div>
<div id="pagination"></div>
<script>
const data = {json.dumps(alle_dokumenter, ensure_ascii=False)};
let perPage = 50;
let currentPage = 1;

function renderPage(page) {{
  const start = (page-1)*perPage;
  const end = start+perPage;
  const items = data.slice(start,end);
  document.getElementById("container").innerHTML = items.map(d =>
    `<div class='card'>
      <h3>${{d.tittel}}</h3>
      <p>${{d.dato}} – ${{d.dokumentID}} – ${{d.mottaker}} (side ${{d.side}})</p>
      <p><a href='${{d.detalj_link}}' target='_blank'>Detaljer</a> | 
         <a href='${{d.detalj_link}}' target='_blank'>Be om innsyn</a></p>
    </div>`
  ).join("");
  document.getElementById("pagination").innerHTML =
    `<button onclick='prevPage()' ${{page===1?"disabled":""}}>Forrige</button>
     Side ${{page}} av ${{Math.ceil(data.length/perPage)}}
     <button onclick='nextPage()' ${{end>=data.length?"disabled":""}}>Neste</button>`;
}}

function prevPage() {{ if(currentPage>1) {{ currentPage--; renderPage(currentPage); }} }}
function nextPage() {{ if(currentPage<Math.ceil(data.length/perPage)) {{ currentPage++; renderPage(currentPage); }} }}

renderPage(currentPage);
</script>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Lagret HTML med paginering til index.html")

if __name__ == "__main__":
    main()
