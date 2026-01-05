import json
from pathlib import Path

ARCHIVE_DIR = Path("data/archive")

def extract_year_from_filename(filename):
    parts = filename.split("_")
    if len(parts) < 2:
        return None
    year = parts[1]
    return int(year) if year.isdigit() else None

def fix_file(path):
    expected_year = extract_year_from_filename(path.name)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    filtered = []
    removed = 0

    for entry in data:
        iso = entry.get("dato_iso")
        if iso and iso.startswith(str(expected_year)):
            filtered.append(entry)
        else:
            removed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    return len(filtered), removed

def main():
    print("=== Fikser arkivfiler ===")
    for file in sorted(ARCHIVE_DIR.glob("postliste_*_H*.json")):
        kept, removed = fix_file(file)
        print(f"\nFil: {file.name}")
        print(f"  Beholdt: {kept}")
        print(f"  Fjernet: {removed}")
        if removed > 0:
            print("  STATUS: ✔ RENSKET")
        else:
            print("  STATUS: OK (ingen feil)")
            
if __name__ == "__main__":
    main()
