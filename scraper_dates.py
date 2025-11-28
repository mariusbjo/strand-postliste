from playwright.sync_api import sync_playwright
import json, os
from datetime import datetime

DATA_FILE = "postliste.json"
BASE_URL = "https://www.strand.kommune.no/.../sok-i-post-dokumenter-og-saker/#/?page={page}&pageSize=100"

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r",encoding="utf-8") as f:
            try: return {d["dokumentID"]:d for d in json.load(f) if "dokumentID" in d}
            except: return {}
    return {}

def save_json(data):
    with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)

def parse_date_robust(s):
    for fmt in ("%d.%m.%Y","%Y-%m-%d"):
        try: return datetime.strptime(s,fmt).date()
        except: continue
    return None

# hent_side kan gjenbrukes fra scraper.py (samme struktur)

def update_json(new_docs):
    updated=load_existing()
    for d in new_docs:
        doc_id=d["dokumentID"]; old=updated.get(doc_id)
        if not old or any(old.get(k)!=d.get(k) for k in ["status","tittel","dokumenttype","avsender_mottaker"]) or len(old.get("filer",[]))!=len(d.get("filer",[])):
            updated[doc_id]=d
            print(f"[{'NEW' if not old else 'UPDATE'}] {doc_id} – {d['tittel']}")
    data_list=sorted(updated.values(),key=lambda x:x.get("dato",""),reverse=True)
    save_json(data_list); print(f"[INFO] Lagret JSON med {len(data_list)} dokumenter")

def main(start_date=None,end_date=None):
    """
    - start_date + end_date → periode
    - bare start_date → spesifikk dato
    - ingen datoer → alt
    """
    print("[INFO] Starter scraper_dates…")
    all_docs=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        page_num=1
        while True:
            docs=hent_side(page_num,browser)
            if not docs: break
            for d in docs:
                dt=parse_date_robust(d["dato"])
                if not dt: continue
                if start_date and end_date:
                    if start_date<=dt<=end_date: all_docs.append(d); print(f"[MATCH] {d['dokumentID']} – {d['dato']}")
                elif start_date:
                    if dt==start_date: all_docs.append(d); print(f"[MATCH] {d['dokumentID']} – {d['dato']}")
                else:
                    all_docs.append(d)
            page_num+=1
        browser.close()
    update_json(all_docs)

if __name__=="__main__":
    # Eksempel: spesifikk dato
    # main(start_date=datetime(2025,11,20).date())
    # Eksempel: periode
     main(start_date=datetime(2025,11,1).date(), end_date=datetime(2025,11,18).date())
    pass
