import json
from datetime import datetime
from pathlib import Path

POSTLISTE_PATH = Path("data/postliste.json")
BACKUP_PATH = Path("data/postliste_backup_before_normalize.json")

REQUIRED_FIELDS = [
    "tittel",
    "dato",
    "dato_iso",
    "dokumentID",
    "dokumenttype",
    "avsender_mottaker",
    "journal_link",
    "filer",
    "status",
]

def parse_date(dato_str):
    """Prøver å parse dato i format DD.MM.YYYY."""
    try:
        return datetime.strptime(dato_str, "%d.%m.%Y").date()
    except Exception:
        return None

def normalize_entry(entry):
    changed = False

    # 1. Fjern felter som ikke skal være der
    for unwanted in ["parsed_date", "side", "detalj_link"]:
        if unwanted in entry:
            del entry[unwanted]
            changed = True

    # 2. Sikre at journal_link finnes (kan ha vært detalj_link)
    if "journal_link" not in entry:
        entry["journal_link"] = ""
        changed = True

    # 3. Sikre at filer er en liste
    if not isinstance(entry.get("filer"), list):
        entry["filer"] = []
        changed = True

    # 4. Sikre at dato finnes
    if not entry.get("dato"):
        if entry.get("dato_iso"):
            try:
                d = datetime.strptime(entry["dato_iso"], "%Y-%m-%d").date()
                entry["dato"] = d.strftime("%d.%m.%Y")
                changed = True
            except:
                pass

    # 5. Sikre dato_iso
    if not entry.get("dato_iso"):
        if entry.get("dato"):
            d = parse_date(entry["dato"])
            if d:
                entry["dato_iso"] = d.strftime("%Y-%m-%d")
                changed = True

    # 6. Valider dato_iso
    try:
        datetime.strptime(entry["dato_iso"], "%Y-%m-%d")
    except:
        entry["dato_iso"] = None
        changed = True

    # 7. Sikre at alle REQUIRED_FIELDS finnes
    for field in REQUIRED_FIELDS:
        if field not in entry:
            if field == "filer":
                entry[field] = []
            else:
                entry[field] = ""
            changed = True

    return changed


def main():
    print("=== Normaliserer postliste.json ===")

    # Backup før endringer
    if POSTLISTE_PATH.exists():
        BACKUP_PATH.write_text(POSTLISTE_PATH.read_text(), encoding="utf-8")
        print(f"[INFO] Backup lagret til {BACKUP_PATH}")

    data = json.loads(POSTLISTE_PATH.read_text(encoding="utf-8"))

    total = len(data)
    changed_count = 0
    removed = 0

    normalized = []

    for entry in data:
        changed = normalize_entry(entry)

        # Fjern oppføringer uten gyldig dato_iso
        if not entry.get("dato_iso"):
            removed += 1
            continue

        if changed:
            changed_count += 1

        normalized.append(entry)

    # Skriv tilbake
    POSTLISTE_PATH.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[INFO] Totalt oppføringer: {total}")
    print(f"[INFO] Endret: {changed_count}")
    print(f"[INFO] Fjernet ugyldige: {removed}")
    print(f"[INFO] Normalisert total: {len(normalized)}")
    print("=== Ferdig ===")


if __name__ == "__main__":
    main()
