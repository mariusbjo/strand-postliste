import json
from pathlib import Path
from datetime import datetime, date

DATA_DIR = Path("data")
LEGACY_FILE = DATA_DIR / "postliste.json"

SHARD_PREFIX = "postliste_"
SHARD_MAX_BYTES = 50 * 1024 * 1024
SHARD_INDEX_FILE = DATA_DIR / "postliste_index.json"


def sort_key(x):
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


def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main():
    if not LEGACY_FILE.exists():
        print("[ERROR] postliste.json finnes ikke. Ingenting å migrere.")
        return

    print(f"[INFO] Leser legacy-fil: {LEGACY_FILE}")

    try:
        data = json.loads(LEGACY_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            print("[ERROR] postliste.json er ikke en liste. Avbryter.")
            return
    except Exception as e:
        print(f"[ERROR] Klarte ikke lese postliste.json: {e}")
        return

    # Dedup basert på dokumentID
    merged = {}
    for d in data:
        if not isinstance(d, dict):
            continue
        did = d.get("dokumentID")
        if not did:
            continue
        merged[did] = d

    docs = list(merged.values())
    docs_sorted = sorted(docs, key=sort_key, reverse=True)

    print(f"[INFO] Totalt {len(docs_sorted)} unike dokumenter etter dedup.")

    # Shard dem ut
    shards = []
    current = []
    current_index = 1

    def current_path(idx):
        return DATA_DIR / f"{SHARD_PREFIX}{idx}.json"

    for doc in docs_sorted:
        current.append(doc)
        serialized = json.dumps(current, ensure_ascii=False)
        if len(serialized.encode("utf-8")) > SHARD_MAX_BYTES:
            last = current.pop()
            path = current_path(current_index)
            atomic_write(path, current)
            shards.append(path)
            print(f"[INFO] Skrev shard {path} med {len(current)} dokumenter.")
            current_index += 1
            current = [last]

    if current:
        path = current_path(current_index)
        atomic_write(path, current)
        shards.append(path)
        print(f"[INFO] Skrev shard {path} med {len(current)} dokumenter.")

    # Skriv index
    atomic_write(SHARD_INDEX_FILE, [p.name for p in shards])

    total = sum(len(json.loads(p.read_text(encoding="utf-8"))) for p in shards)
    print(f"[INFO] Ferdig: {total} dokumenter fordelt på {len(shards)} shards.")
    print("[INFO] Migrering fullført. postliste.json kan beholdes eller slettes.")


if __name__ == "__main__":
    main()
