import os
import json
from datetime import datetime, date
from pathlib import Path

# Standard paths used av scraper.py
DATA_DIR = "../../data"
CHANGES_FILE = "../../data/changes.json"


def ensure_directories():
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def ensure_file(path, default):
    """Oppretter fil med default-innhold hvis den ikke finnes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")


def load_config(path):
    """Laster config-fil, oppretter default hvis mangler."""
    ensure_file(path, {
        "start_page": 1,
        "max_pages": 100,
        "per_page": 100
    })
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_existing(path):
    """
    Leser eksisterende postliste.json og returnerer dict:
    { dokumentID: oppføring }
    """
    ensure_file(path, [])
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return {}
        return {d["dokumentID"]: d for d in data if isinstance(d, dict)}
    except Exception:
        return {}


def atomic_write(path, data):
    """Skriver JSON atomisk for å unngå korrupte filer."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def merge_and_save(existing, new_docs, path):
    """Slår sammen eksisterende og nye dokumenter og lagrer sortert."""
    updated = dict(existing)
    for d in new_docs:
        updated[d["dokumentID"]] = d

    def sort_key(x):
        # Prøv dato_iso (ISO-format) først, deretter dato (DD.MM.YYYY), ellers date.min
        for key in ("dato_iso", "dato"):
            v = x.get(key)
            if not v:
                continue
            try:
                if key == "dato_iso":
                    return datetime.fromisoformat(v).date()
                else:
                    return datetime.strptime(v, "%d.%m.%Y").date()
            except Exception:
                continue
        return date.min

    data_list = sorted(updated.values(), key=sort_key, reverse=True)
    atomic_write(path, data_list)
    print(f"[INFO] Lagret JSON med {len(data_list)} dokumenter")


# ---------------------------------------------------------
#   Endringslogg-funksjoner for incremental scraper
# ---------------------------------------------------------

def load_changes():
    """Laster tidligere endringslogg fra changes.json."""
    path = Path(CHANGES_FILE)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_changes(changes):
    """Lagrer endringslogg til changes.json."""
    path = Path(CHANGES_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(changes, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[INFO] Lagret {len(changes)} endringshendelser i {CHANGES_FILE}")
