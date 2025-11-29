import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

DATA_FILE = "data/postliste.json"
CONFIG_FILE = "config.json"
OUTPUT_FILE = "web/index.html"
TEMPLATE_FILE = "web/template.html"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                pass
    return {"per_page": 50}

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def generate_html():
    data = load_data()
    config = load_config()
    per_page = int(config.get("per_page", 50))
    updated = datetime.now(ZoneInfo("Europe/Oslo")).strftime("%d.%m.%Y %H:%M")

    # Les template.html
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()

    # Sett inn variabler
    html = template.format(
        updated=updated,
        per_page=per_page,
        data_json=json.dumps(data, ensure_ascii=False)
    )

    # Lagre ferdig index.html
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[INFO] Lagret HTML til {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_html()
