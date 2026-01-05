import os, json
from datetime import datetime, date

def ensure_directories():
    os.makedirs("../../data", exist_ok=True)

def ensure_file(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

def load_config(path):
    ensure_file(path, {
        "start_page": 1,
        "max_pages": 100,
        "per_page": 100
    })
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_existing(path):
    ensure_file(path, [])
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                return {}
            return {d["dokumentID"]: d for d in data if isinstance(d, dict)}
    except:
        return {}

def atomic_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def merge_and_save(existing, new_docs, path):
    updated = dict(existing)
    for d in new_docs:
        updated[d["dokumentID"]] = d

    def sort_key(x):
        try:
            return datetime.strptime(x.get("dato"), "%d.%m.%Y").date()
        except:
            return date.min

    data_list = sorted(updated.values(), key=sort_key, reverse=True)
    atomic_write(path, data_list)
    print(f"[INFO] Lagret JSON med {len(data_list)} dokumenter")
