import requests

url = "https://www.strand.kommune.no/api/presentation/v2/nye-innsyn/overview"
r = requests.get(url)
print("Status:", r.status_code)
print("Keys:", r.json().keys())

# Skriv ut første element hvis det finnes
items = r.json().get("items") or r.json().get("hits") or []
if items:
    print("Første oppføring:", items[0])
