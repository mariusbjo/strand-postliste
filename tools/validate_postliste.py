import json
from datetime import datetime
from pathlib import Path

POSTLISTE_PATH = Path("data/postliste.json")

REQUIRED_FIELDS = {
    "tittel": str,
    "dato": str,
    "dato_iso": str,
    "dokumentID": str,
    "dokumenttype": str,
    "avsender_mottaker": str,
    "journal_link": str,
    "filer": list,
    "status": str,
}

def validate_date_iso(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except:
        return False

def validate_date(value):
    try:
        datetime.strptime(value, "%d.%m.%Y")
        return True
    except:
        return False

def main():
    print("=== Validerer postliste.json ===")

    data = json.loads(POSTLISTE_PATH.read_text(encoding="utf-8"))

    total = len(data)
    missing_fields = 0
    wrong_types = 0
    invalid_dates = 0
    unknown_fields = 0

    for idx, entry in enumerate(data):
        # 1. Sjekk ukjente felter
        for key in entry.keys():
            if key not in REQUIRED_FIELDS:
                print(f"[UKJENT FELT] Oppføring {idx}: '{key}'")
                unknown_fields += 1

        # 2. Sjekk manglende felter
        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in entry:
                print(f"[MANGLER] Oppføring {idx}: '{field}' mangler")
                missing_fields += 1
                continue

            # 3. Sjekk type
            if not isinstance(entry[field], expected_type):
                print(f"[FEIL TYPE] Oppføring {idx}: '{field}' skal være {expected_type.__name__}")
                wrong_types += 1

        # 4. Sjekk datoformat
        if "dato" in entry and not validate_date(entry["dato"]):
            print(f"[UGYLDIG dato] Oppføring {idx}: '{entry['dato']}'")
            invalid_dates += 1

        if "dato_iso" in entry and not validate_date_iso(entry["dato_iso"]):
            print(f"[UGYLDIG dato_iso] Oppføring {idx}: '{entry['dato_iso']}'")
            invalid_dates += 1

    print("\n=== RESULTAT ===")
    print(f"Totalt oppføringer: {total}")
    print(f"Manglende felter: {missing_fields}")
    print(f"Feil datatyper: {wrong_types}")
    print(f"Ugyldige datoer: {invalid_dates}")
    print(f"Ukjente felter: {unknown_fields}")

    if missing_fields == 0 and wrong_types == 0 and invalid_dates == 0 and unknown_fields == 0:
        print("\nSTATUS: ✔ Datasettet er gyldig og konsistent")
    else:
        print("\nSTATUS: ❗ Datasettet har problemer som bør fikses")

if __name__ == "__main__":
    main()
