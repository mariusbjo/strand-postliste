import json
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("data")
SHARD_INDEX = DATA_DIR / "postliste_index.json"


def load_json_list(path: Path):
    """Trygt les en JSON-liste fra fil."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        print(f"[WARN] Filen {path} inneholder ikke en liste – hopper over.")
        return []
    except Exception as e:
        print(f"[WARN] Klarte ikke lese {path}: {e}")
        return []


def main():
    print("=== Søker etter duplikater i shard-filer ===")

    if not SHARD_INDEX.exists():
        print("[ERROR] postliste_index.json finnes ikke. Ingen shards å analysere.")
        return

    # 1. Last index
    try:
        shard_files = json.loads(SHARD_INDEX.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Klarte ikke lese shard-index: {e}")
        return

    if not isinstance(shard_files, list):
        print("[ERROR] postliste_index.json har feil format (forventer liste).")
        return

    # 2. Last alle shards
    seen = defaultdict(list)  # dokid -> [(filnavn, indeks)]
    total_entries = 0

    for shard_name in shard_files:
        shard_path = DATA_DIR / shard_name

        if not shard_path.exists():
            print(f"[WARN] Shard mangler: {shard_path}")
            continue

        entries = load_json_list(shard_path)

        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue

            dokid = entry.get("dokumentID")
            if dokid:
                seen[dokid].append((shard_name, idx))

        total_entries += len(entries)

    print(f"[INFO] Totalt lastet {total_entries} oppføringer fra {len(shard_files)} shards.")

    # 3. Finn duplikater
    duplicates = {dokid: locs for dokid, locs in seen.items() if len(locs) > 1}

    if not duplicates:
        print("✔ Ingen duplikater funnet i shard-systemet.")
        return

    print(f"\n❗ Fant {len(duplicates)} duplikat-IDer:\n")

    for dokid, locations in duplicates.items():
        print(f"- dokumentID '{dokid}' forekommer {len(locations)} ganger:")
        for shard_name, idx in locations:
            print(f"    • {shard_name} [indeks {idx}]")

    print("\nSTATUS: ❗ Duplikater må håndteres")


if __name__ == "__main__":
    main()
