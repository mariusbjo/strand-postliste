import json
from pathlib import Path

DATA_DIR = Path("data")
LEGACY_FILE = DATA_DIR / "postliste.json"
SHARD_PREFIX = "postliste_"
SHARD_INDEX_FILE = DATA_DIR / "postliste_index.json"


def load_json_list(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print(f"[WARN] Klarte ikke lese {path}: {e}")
        return []


def main():
    print("=== Verifiserer migrering av postliste.json → postliste_N.json ===")

    if not LEGACY_FILE.exists():
        print("[ERROR] postliste.json finnes ikke. Ingenting å verifisere.")
        return

    # 1. Last legacy-data
    legacy_docs = load_json_list(LEGACY_FILE)
    legacy_ids = {d.get("dokumentID") for d in legacy_docs if isinstance(d, dict)}
    print(f"[INFO] Legacy: {len(legacy_ids)} dokumenter funnet i postliste.json")

    # 2. Last shard-index
    if not SHARD_INDEX_FILE.exists():
        print("[ERROR] postliste_index.json finnes ikke. Migrering er ikke kjørt.")
        return

    try:
        shard_names = json.loads(SHARD_INDEX_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Klarte ikke lese shard-index: {e}")
        return

    shard_paths = [DATA_DIR / name for name in shard_names]

    # 3. Last alle shard-dokumenter
    shard_ids = set()
    for path in shard_paths:
        docs = load_json_list(path)
        for d in docs:
            if isinstance(d, dict):
                did = d.get("dokumentID")
                if did:
                    shard_ids.add(did)

    print(f"[INFO] Shards: {len(shard_ids)} dokumenter funnet i postliste_N.json")

    # 4. Sammenlign
    missing = legacy_ids - shard_ids
    extra = shard_ids - legacy_ids

    if missing:
        print("\n❌ FEIL: Følgende dokumenter mangler i shard-systemet:")
        for did in sorted(missing):
            print("   -", did)
    else:
        print("\n✔ Ingen dokumenter mangler i shard-systemet.")

    if extra:
        print("\nℹ Info: Shard-systemet inneholder dokumenter som ikke finnes i legacy:")
        for did in sorted(extra):
            print("   -", did)

    # 5. Endelig status
    if not missing:
        print("\n🎉 VERIFISERT: Alle legacy-dokumenter finnes i shard-systemet.")
        print("   Det er trygt å slette postliste.json.")
    else:
        print("\n⚠ VERIFIKASJON FEILET: Ikke slett postliste.json ennå.")


if __name__ == "__main__":
    main()
