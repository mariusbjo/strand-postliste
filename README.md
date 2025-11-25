# Strand kommune – uoffisiell postliste

Dette prosjektet speiler postlisten til Strand kommune ved hjelp av en automatisert scraper.  
Målet er å gjøre dokumentoversikten enklere tilgjengelig, og å tilby en uoffisiell HTML‑ og JSON‑versjon.

## 🚀 Hvordan det fungerer

- **Playwright (Python)** brukes til å starte en headless Chromium‑nettleser.
- Nettleseren laster inn postlisten side for side (opptil 200 sider).
- Hver oppføring hentes ut med tittel, dato, dokumentID, mottaker og detaljlenke.
- Resultatet lagres i:
  - `postliste.json` – strukturert data
  - `index.html` – enkel webside med kortvisning

## 📄 Funksjoner

- **Klikkbare lenker** til hver oppføring i kommunens postliste.
- **“Be om innsyn”‑knapp** som tar deg direkte til oppføringen i kommunens innsynsløsning, slik at du kan legge dokumentet til en samlet bestilling.
- **Progress‑logg** i GitHub Actions som viser antall dokumenter per side og total hittil.
- **Automatisk oppdatering**: GitHub Actions kjører daglig og pusher oppdatert `index.html` og `postliste.json` til `main`.

## ⚙️ Workflow

Se `.github/workflows/publish.yml` for detaljer.  
Workflowen:
1. Sjekker ut repo
2. Installerer Python og Playwright
3. Kjører `scraper.py`
4. Commiter og pusher genererte filer

## 📂 Output

- `index.html` – en enkel webside med alle dokumentene.
- `postliste.json` – maskinlesbar oversikt over dokumentene.

## ⚠️ Merknad

Dette er en uoffisiell speiling.  
For innsyn i dokumenter som ikke er publisert, bruk “Be om innsyn”‑knappen som tar deg til kommunens offisielle innsynsløsning.
