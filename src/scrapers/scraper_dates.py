from playwright.sync_api import sync_playwright
import json, os, time, sys, argparse
from datetime import datetime, date

# ------------------------------
# ARGUMENTPARSING (STRATEGI A)
# ------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="../config/config.json")
parser.add_argument("start_date", nargs="?")
parser.add_argument("end_date", nargs="?")
args = parser.parse_args()

CONFIG_FILE = args.config
DATA_FILE = "../../data/postliste.json"

BASE_URL = (
    "https://www.strand.kommune.no/tjenester/politikk-innsyn-og-medvirkning/"
    "postliste-dokumenter-og-vedtak/sok-i-post-dokumenter-og-saker/"
    "#/?page={page}&pageSize={page_size}"
)

# ------------------------------
# SELVHELBREDENDE FILSYSTEM
# ------------------------------

def ensure_directories():
    os.makedirs("../../data", exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

def ensure_file(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

# ------------------------------
# LASTING AV KONFIG OG DATA
# ------------------------------

def load_config():
    ensure_file(CONFIG_FILE, {
        "start_page": 1,
        "max_pages": 100,
        "per_page": 100
    })
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_existing():
    ensure_file(DATA_FILE, [])
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {d["dokumentID"]: d for d in data if "dokumentID" in d}
    except Exception:
        return {}

# ------------------------------
# ATOMISK SKRIVING
# ------------------------------

def atomic_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

# ------------------------------
# UTILITY
# ------------------------------

def safe_text(el, sel):
    try:
        node = el.query_selector(sel)
        return node.inner_text().strip() if node else ""
    except:
        return ""

def parse_dato_str(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except:
            pass
    try:
        return datetime.fromisoformat(s[:10]).date()
    except:
        return None

def format_dato_ddmmYYYY(d):
    return d.strftime("%d.%m.%Y") if d else ""

# ------------------------------
# HENT ÉN SIDE
# ------------------------------

def hent_side(page_num, browser, per_page):
    url = BASE_URL.format(page=page_num, page_size=per_page)
    print(f"[INFO] Åpner side {page_num}: {url}")

    page = browser.new_page()

    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(5)
        page.wait_for_selector("article.bc-content-teaser--item", timeout=30000)
    except Exception:
        print("[WARN] Ingen artikler funnet på denne siden.")
        page.close()
        return []

    docs = []

    for art in page.query_selector_all("article.bc-content-teaser--item"):
        dokid = safe_text(art, ".bc-content-teaser-meta-property--dokumentID dd")
        if not dokid:
            continue

        tittel = safe_text(art, ".bc-content-teaser-title-text")
        dato_str = safe_text(art, ".bc-content-teaser-meta-property--dato dd")
        parsed_date = parse_dato_str(dato_str)
        doktype = safe_text(art, ".SakListItem_sakListItemTypeText__16759c")
        avsender = safe_text(art, ".bc-content-teaser-meta-property--avsender dd")
        mottaker = safe_text(art, ".bc-content-teaser-meta-property--mottaker dd")

        am = (
            f"Avsender: {avsender}"
            if avsender else (f"Mottaker: {mottaker}" if mottaker else "")
        )

        detalj_link = ""
        try:
            link_elem = art.evaluate_handle("node => node.closest('a')")
            detalj_link = link_elem.get_attribute("href") if link_elem else ""
        except:
            pass

        if detalj_link and not detalj_link.startswith("http"):
            detalj_link = "https://www.strand.kommune.no" + detalj_link

        filer = []
        if detalj_link:
            dp = browser.new_page()
            try:
                dp.goto(detalj_link, timeout=60000, wait_until="domcontentloaded")
                time.sleep(2)
                for fl in dp.query_selector_all("a"):
                    href, tekst = fl.get_attribute("href"), fl.inner_text()
                    if href and "/api/presentation/v2/nye-innsyn/filer" in href:
                        abs_url = (
                            href if href.startswith("http")
                            else "https://www.strand.kommune.no" + href
                        )
                        filer.append({"tekst": tekst.strip(), "url": abs_url})
            finally:
                dp.close()

        status = "Publisert" if filer else "Må bes om innsyn"

        docs.append({
            "tittel": tittel,
            "dato": format_dato_ddmmYYYY(parsed_date),
            "dato_iso": parsed_date.isoformat() if parsed_date else None,
            "dokumentID": dokid,
            "dokumenttype": doktype,
            "avsender_mottaker": am,
            "journal_link": detalj_link,
            "filer": filer,
            "status": status
        })

    page.close()
    print(f"[INFO] Fant {len(docs)} dokumenter på side {page_num}.")
    return docs

# ------------------------------
# HOVEDLOGIKK
# ------------------------------

def within_range(d, start_date, end_date):
    if not d:
        return False
    if start_date and d < start_date:
        return False
    if end_date and d > end_date:
        return False
    return True

def update_json(new_docs):
    existing = load_existing()
    updated = dict(existing)

    for d in new_docs:
        doc_id = d["dokumentID"]
        old = updated.get(doc_id)

        if not old:
            print(f"[NEW] {doc_id} – {d['tittel']}")
        elif old != d:
            print(f"[UPDATE] {doc_id} – {d['tittel']}")

        updated[doc_id] = d

    def sort_key(x):
        try:
            return datetime.strptime(x.get("dato"), "%d.%m.%Y").date()
        except:
            return date.min

    data_list = sorted(updated.values(), key=sort_key, reverse=True)

    atomic_write(DATA_FILE, data_list)
    print(f"[INFO] Lagret JSON med {len(data_list)} dokumenter")

def main(start_date=None, end_date=None):
    print("[INFO] Starter scraper_dates…")

    ensure_directories()

    cfg = load_config()
    start_page = int(cfg.get("start_page", 1))
    max_pages = int(cfg.get("max_pages", 100))
    per_page = int(cfg.get("per_page", 100))

    print(f"[INFO] Konfigurasjon:")
    print(f"       start_page = {start_page}")
    print(f"       max_pages  = {max_pages}")
    print(f"       per_page   = {per_page}")
    print(f"       start_date = {start_date}")
    print(f"       end_date   = {end_date}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])

        all_docs = []
        page_num = start_page

        while page_num <= max_pages:
            docs = hent_side(page_num, browser, per_page)

            if not docs:
                print(f"[INFO] Ingen dokumenter på side {page_num}, stopper.")
                break

            for d in docs:
                pd = parse_dato_str(d.get("dato"))
                if within_range(pd, start_date, end_date):
                    all_docs.append(d)

            parsed_on_page = [
                parse_dato_str(x.get("dato")) for x in docs if x.get("dato")
            ]
            if start_date and parsed_on_page and all(
                x and x < start_date for x in parsed_on_page
            ):
                print("[INFO] Tidlig stopp: alle datoer på siden er eldre enn start_date")
                break

            page_num += 1

        browser.close()

    print(f"[INFO] Totalt hentet {len(all_docs)} dokumenter innenfor dato-range.")
    update_json(all_docs)

# ------------------------------
# CLI
# ------------------------------

if __name__ == "__main__":
    sd = args.start_date
    ed = args.end_date

    start_date = datetime.strptime(sd, "%Y-%m-%d").date() if sd else None
    end_date = datetime.strptime(ed, "%Y-%m-%d").date() if ed else None

    if start_date and not end_date:
        end_date = start_date

    main(start_date=start_date, end_date=end_date)
