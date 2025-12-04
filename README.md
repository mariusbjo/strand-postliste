# Strand kommune postliste-scraper

Dette prosjektet automatiserer innhenting og publisering av kommunens postliste (journalposter) ved hjelp av Python-scrapere og GitHub Actions.  
Systemet håndterer både daglige oppdateringer og full historisk scraping.

## 🚀 Funksjoner

- **Daglig scraping (incremental)**  
  - Workflow: `morgen.yml`  
  - Kjører hver morgen kl. 06:00.  
  - Henter nye oppføringer og oppdaterer eksisterende.  
  - Bruker `scraper.py` i *incremental*-modus.

- **Oppdaterings-scraping (update)**  
  - Workflow: `oppdatering.yml`  
  - Kan kjøres manuelt eller planlagt.  
  - Går gjennom de siste 50 sidene (konfigurerbart).  
  - Henter både nye oppføringer og oppdaterer eksisterende.

- **Publisering (HTML)**  
  - Workflow: `publish.yml`  
  - Genererer `index.html` fra `postliste.json`.  
  - Publiserer oppdatert postliste som statisk HTML.

- **Full historisk scraping**  
  - Workflow: `fullscrape.yml`  
  - Brukes til å hente hele år eller halvår.  
  - Benytter `scraper_dates.py` med dato-intervall.  
  - Resultat lagres i `archive/` som egne JSON-filer (f.eks. `postliste_2006_H1.json`).

## ⚙️ Konfigurasjon

Alle scrapere leser innstillinger fra `config.json`.  
Eksempel på innhold:

```json
{
  "mode": "incremental",
  "max_pages_incremental": 10,
  "max_pages_update": 50,
  "max_pages_full": 200,
  "per_page": 100
}

mode: styrer hvordan scraperen kjører (incremental, update, full).
max_pages_incremental: antall sider som sjekkes i daglig scraping.
max_pages_update: antall sider som sjekkes i oppdateringsmodus.
max_pages_full: antall sider som sjekkes i full scraping.
per_page: antall oppføringer per side (100 anbefales).
For fullscrape.yml brukes en egen config_fullscrape.json slik at config.json for daglig drift ikke overskrives.

---

### 4. Scrapere
```markdown
## 🐍 Scrapere

### `scraper.py`
- Brukes av `morgen.yml`.  
- Kjører i incremental-modus.  
- Stopper først når alle oppføringer på en side er kjente.  
- Henter både nye og oppdaterte oppføringer.

### `scraper_dates.py`
- Brukes av `fullscrape.yml`.  
- Kjører i full-modus.  
- Tar inn dato eller periode som argument:
  ```bash
  python scraper_dates.py 2025-12-01
  python scraper_dates.py 2025-01-01 2025-12-31

## 📂 Filstruktur
├── archive/ # Historiske JSON-filer (fullscrape)
├── postliste.json # Hovedfil med siste oppføringer
├── index.html # Generert HTML fra postliste.json
├── scraper.py # Incremental scraper
├── scraper_dates.py # Full scraper med dato-intervall
├── generate_html.py # Lager HTML fra JSON
├── config.json # Daglig konfigurasjon
├── config_fullscrape.json # Fullscrape-konfigurasjon
└── .github/workflows/ # GitHub Actions workflows

## 🔄 Workflows

- **morgen.yml** → daglig incremental scraping + HTML.  
- **oppdatering.yml** → manuell eller planlagt update-scraping.  
- **publish.yml** → genererer og publiserer HTML.  
- **fullscrape.yml** → full historisk scraping (halvår/år).

## 📊 Output

- JSON-filer (`postliste.json` og arkivfiler) med alle oppføringer.  
- HTML (`index.html`) som viser postlisten i lesbart format.  
- Oppføringer inneholder:
  - `tittel`
  - `dato` (dd.mm.yyyy)
  - `parsed_date` (ISO)
  - `dokumentID`
  - `dokumenttype`
  - `avsender_mottaker`
  - `journal_link`
  - `filer`
  - `status`

## 🛠️ Bruk

- Daglig drift skjer automatisk via GitHub Actions.  
- Fullscrape trigges manuelt via `workflow_dispatch`.  
- Alle endringer commit‑tes og pushes automatisk til repoet.

## 📌 Viktig

- **Incremental-modus** stopper først når alle oppføringer på en side er kjente.  
- **Update-modus** henter både nye og oppdaterte oppføringer.  
- **Full-modus** brukes for historiske perioder og henter opptil 200 sider.  
- `config.json` er den eneste kilden til sannhet for scraper‑innstillinger.
