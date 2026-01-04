from playwright.sync_api import sync_playwright
import json, os, time
from datetime import datetime, date

CONFIG_FILE = "src/config/config.json"
DATA_FILE = "data/postliste.json"
CHANGES_FILE = "data/changes.json"

BASE_URL = (
    "https://www.strand.kommune.no/tjenester/politikk-innsyn-og-medvirkning/"
    "postliste-dokumenter-og-vedtak/sok-i-post-dokumenter-og-saker/#/"
    "?page={page}&pageSize=100"
)


# ---------------------------
#  SELVHELBREDENDE FILSYSTEM
# ---------------------------

def ensure_directories():
    os.makedirs("data", exist_ok=True)
    os.makedirs("src/config", exist_ok=True)


def ensure_file(path, default):
    if not os.path.exists(path):
        print(f"[INFO] Oppretter manglende fil: {path}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)


# ---------------------------
#  LASTING AV KONFIG OG DATA
# ---------------------------

def load_config():
    ensure_file(
        CONFIG_FILE,
        {
            "mode": "incremental",
            "max_pages_incremental": 10,
            "max_pages_update": 200,
            "max_pages_full": 500,
            "per_page": 50,
        },
    )
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg if isinstance(cfg, dict) else {}
    except Exception as e:
        print(f"[ERROR] Klarte ikke lese config, bruker fallback: {e}")
        return {
            "mode": "incremental",
            "max_pages_incremental": 10,
            "max_pages_update": 200,
            "max_pages_full": 500,
            "per_page": 50,
        }


def load_existing():
    ensure_file(DATA_FILE, [])
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                print("[WARN] DATA_FILE er ikke en liste. Ignorerer innhold.")
                return {}
            return {d["dokumentID"]: d for d in data if isinstance(d, dict) and "dokumentID" in d}
    except Exception as e:
        print(f"[ERROR] Klarte ikke lese eksisterende data, starter tomt: {e}")
        return {}


def load_changes():
    ensure_file(CHANGES_FILE, [])
    try:
        with open(CHANGES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[ERROR] Klarte ikke lese changes, starter med tom liste: {e}")
        return []


# ---------------------------
#  LAGRING (ATOMISK)
# ---------------------------

def atomic_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def save_changes(changes):
    try:
        atomic_write(CHANGES_FILE, changes)
    except Exception as e:
        print(f"[ERROR] Klarte ikke lagre changes: {e}")


# ---------------------------
#  ROBUST NAVIGASJON
# ---------------------------

def safe_goto(page, url, retries=4, wait="domcontentloaded"):
    """
    Robust wrapper rundt page.goto med retries og backoff.
    Returnerer True hvis siden ble lastet, ellers False.
    """
    for attempt in range(1, retries + 1):
        try:
            page.goto(url, timeout=60000, wait_until=wait)
            return True
        except Exception as e:
            print(f"[WARN] goto-feil (forsøk {attempt}/{retries}) mot {url}: {e}")
            if attempt < retries:
                # eksponentiell backoff
                sleep_s = 2 * attempt
                print(f"[INFO] Venter {sleep_s} sekunder før nytt forsøk...")
                time.sleep(sleep_s)
            else:
                print(f"[ERROR] Klarte ikke åpne URL etter {retries} forsøk: {url}")
                return False


# ---------------------------
#  SCRAPING-UTILS
# ---------------------------

def safe_text(el, sel):
    try:
        node = el.query_selector(sel)
        return node.inner_text().strip() if node else ""
    except Exception:
        return ""


def parse_dato(s):
    if not s:
        return None, None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(s, fmt).date()
            return dt.strftime("%d.%m.%Y"), dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    try:
        dt = datetime.fromisoformat(s[:10]).date()
        return dt.strftime("%d.%m.%Y"), dt.strftime("%Y-%m-%d")
    except Exception:
        return None, None


# ---------------------------
#  HENT ENKELT SIDE
# ---------------------------

def hent_side(page_num, browser):
    url = BASE_URL.format(page=page_num)
    print(f"[INFO] Åpner side {page_num} ({url})")

    page = browser.new_page()

    # Robust goto for listesiden
    if not safe_goto(page, url):
        page.close()
        return []

    # Vent på artikler, med ett ekstra forsøk hvis det ser tomt ut
    try:
        page.wait_for_selector("article.bc-content-teaser--item", timeout=15000)
    except Exception:
        print(f"[WARN] Ingen artikler funnet på side {page_num} – prøver én gang til...")
        time.sleep(2)
        if not safe_goto(page, url):
            page.close()
            return []
        try:
            page.wait_for_selector("article.bc-content-teaser--item", timeout=15000)
        except Exception:
            print(f"[ERROR] Side {page_num} er tom eller feilet to ganger. Stopper på denne siden.")
            page.close()
            return []

    time.sleep(1)  # stabilisering for SPA

    docs = []
    artikler = page.query_selector_all("article.bc-content-teaser--item")
    print(f"[INFO] Fant {len(artikler)} artikler på side {page_num}")

    for art in artikler:
        dokid = safe_text(art, ".bc-content-teaser-meta-property--dokumentID dd")
        if not dokid:
            continue

        tittel = safe_text(art, ".bc-content-teaser-title-text")
        dato_raw = safe_text(art, ".bc-content-teaser-meta-property--dato dd")
        dato_norsk, dato_iso = parse_dato(dato_raw)
        doktype = safe_text(art, ".SakListItem_sakListItemTypeText__16759c")
        avsender = safe_text(art, ".bc-content-teaser-meta-property--avsender dd")
        mottaker = safe_text(art, ".bc-content-teaser-meta-property--mottaker dd")
        am = f"Avsender: {avsender}" if avsender else (f"Mottaker: {mottaker}" if mottaker else "")

        detalj_link = ""
        filer = []

        # Finn detaljlenke
        try:
            link_elem = art.evaluate_handle("node => node.closest('a')")
            detalj_link = link_elem.get_attribute("href") if link_elem else ""
        except Exception as e:
            print(f"[WARN] Klarte ikke hente detalj-lenke for {dokid}: {e}")
            detalj_link = ""

        # Hent filer via detaljsiden, robust
        if detalj_link:
            dp = browser.new_page()
            if safe_goto(dp, detalj_link):
                time.sleep(1)
                try:
                    for fl in dp.query_selector_all("a"):
                        href = fl.get_attribute("href")
                        tekst = fl.inner_text()
                        if href and "/api/presentation/v2/nye-innsyn/filer" in href:
                            abs_url = href if href.startswith("http") else "https://www.strand.kommune.no" + href
                            filer.append({"tekst": (tekst or "").strip(), "url": abs_url})
                except Exception as e:
                    print(f"[WARN] Klarte ikke hente filer for {dokid}: {e}")
            else:
                print(f"[ERROR] Hopper over detaljside for {dokid} – kunne ikke åpnes.")
            dp.close()

        status = "Publisert" if filer else "Må bes om innsyn"

        docs.append(
            {
                "tittel": tittel,
                "dato": dato_norsk or "",
                "dato_iso": dato_iso,
                "dokumentID": dokid,
                "dokumenttype": doktype,
                "avsender_mottaker": am,
                "side": page_num,
                "detalj_link": detalj_link,
                "filer": filer,
                "status": status,
            }
        )

    page.close()
    return docs


# ---------------------------
#  HOVEDFUNKSJON
# ---------------------------

def main():
    print("[INFO] Starter scraper…")

    ensure_directories()
    config = load_config()
    mode = config.get("mode", "incremental")
    max_pages = int(config.get(f"max_pages_{mode}", 50))

    print(f"[INFO] Modus: {mode}, max_pages: {max_pages}")

    # Last eksisterende data
    existing = load_existing()
    updated = dict(existing)
    changes = load_changes()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])

        for page_num in range(1, max_pages + 1):
            docs = hent_side(page_num, browser)

            if docs is None:
                print(f"[ERROR] hent_side returnerte None for side {page_num} – stopper.")
                break

            if len(docs) == 0:
                print(f"[INFO] Ingen dokumenter på side {page_num}. Stopper.")
                break

            print(f"[INFO] Behandler {len(docs)} dokumenter fra side {page_num}")

            for d in docs:
                doc_id = d["dokumentID"]
                old = updated.get(doc_id)

                if not old:
                    # NYTT dokument
                    updated[doc_id] = d
                    changes.append(
                        {
                            "tidspunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "type": "NEW",
                            "dokumentID": doc_id,
                            "tittel": d.get("tittel"),
                            "endringer": {
                                "status": {"gammel": None, "ny": d.get("status")},
                                "tittel": {"gammel": None, "ny": d.get("tittel")},
                                "dokumenttype": {"gammel": None, "ny": d.get("dokumenttype")},
                                "avsender_mottaker": {"gammel": None, "ny": d.get("avsender_mottaker")},
                                "detalj_link": {"gammel": None, "ny": d.get("detalj_link")},
                                "dato": {"gammel": None, "ny": d.get("dato")},
                                "dato_iso": {"gammel": None, "ny": d.get("dato_iso")},
                                "filer_count": {"gammel": 0, "ny": len(d.get("filer", []))},
                            },
                        }
                    )
                    print(f"[NEW] {doc_id} – {d.get('tittel', '')}")

                else:
                    # OPPDATERING av eksisterende
                    per_change = {}
                    for key in [
                        "status",
                        "tittel",
                        "dokumenttype",
                        "avsender_mottaker",
                        "detalj_link",
                        "dato",
                        "dato_iso",
                    ]:
                        if old.get(key) != d.get(key):
                            per_change[key] = {"gammel": old.get(key), "ny": d.get(key)}

                    if len(old.get("filer", [])) != len(d.get("filer", [])):
                        per_change["filer_count"] = {
                            "gammel": len(old.get("filer", [])),
                            "ny": len(d.get("filer", [])),
                        }

                    if per_change:
                        changes.append(
                            {
                                "tidspunkt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "type": "UPDATE",
                                "dokumentID": doc_id,
                                "tittel": d.get("tittel"),
                                "endringer": per_change,
                            }
                        )
                        print(f"[UPDATE] {doc_id} – {', '.join(per_change.keys())}")

                    updated[doc_id] = d

            # Incremental stoppelogikk
            if mode == "incremental":
                known = sum(1 for d in docs if d["dokumentID"] in existing)
                if known == len(docs):
                    print(
                        "[INFO] Incremental: alle dokumenter på denne siden er kjente "
                        f"({known}/{len(docs)}). Stopper."
                    )
                    break
                else:
                    print(
                        f"[INFO] Incremental: {known}/{len(docs)} dokumenter på denne siden var kjente. Fortsetter."
                    )

        browser.close()

    # ---------------------------
    #  ATOMISK MERGING OG LAGRING
    # ---------------------------

    # Last inn eksisterende data på nytt (i tilfelle annen workflow har oppdatert filen)
    latest_existing = load_existing()

    # Merge
    latest_existing.update(updated)

    # Sorter
    def sort_key(x):
        try:
            return datetime.strptime(x.get("dato"), "%d.%m.%Y").date()
        except Exception:
            return date.min

    data_list = sorted(latest_existing.values(), key=sort_key, reverse=True)

    # Lagre atomisk
    try:
        atomic_write(DATA_FILE, data_list)
    except Exception as e:
        print(f"[ERROR] Klarte ikke lagre {DATA_FILE}: {e}")

    save_changes(changes)

    print(f"[INFO] Lagret JSON med {len(data_list)} dokumenter")
    print(f"[INFO] Logget {len(changes)} endringshendelser i {CHANGES_FILE}")


if __name__ == "__main__":
    main()
