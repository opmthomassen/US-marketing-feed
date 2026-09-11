# Smartly feed preprocessor — Drammens Teater

Regenererer Facebook/Smartly-feeden hver time slik at hvert annonsesett
(kategori) automatisk kan **pauses eller aktiveres** basert på antall
kommende arrangement i kategorien.

## Hva skriptet gjør

1. Henter kilde-CSV fra Drammens Teater.
2. **Eksploderer** rader med flere kategorier til én rad per
   `(arrangement × kategori)`. Slik blir hver kategori en gruppe Smartly kan
   telle og lage carousel over.
3. Teller antall arrangement per kategori.
4. Legger til tre kolonner:
   - `Kategori` — enkeltkategorien for raden (bruk denne til å splitte annonsesett)
   - `event_count_in_category` — antall arrangement i kategorien
   - `ad_set_status` — `ACTIVE` hvis antallet ≥ terskel, ellers `PAUSED`

Resultatet skrives til `output/facebook_smartly.csv`.

## Feed-URL til Smartly

Etter første kjøring peker du Smartly til råfila:

```
https://raw.githubusercontent.com/<BRUKER>/<REPO>/main/output/facebook_smartly.csv
```

I Smartly:
- Splitt annonsesett på feltet **`Kategori`** (ikke `Kategorier`).
- Sett **Ad set → Status → From feed** og velg **`ad_set_status`**.

> Vil du ha en penere/stabil URL kan du i stedet slå på GitHub Pages og
> servere fra `output/` — se nederst.

## Oppsett

1. Opprett et nytt (gjerne privat) GitHub-repo og push disse filene.
2. Gå til **Settings → Actions → General → Workflow permissions** og velg
   **Read and write permissions** (så bot-en får committe feeden tilbake).
3. Gå til **Actions**-fanen, velg *Update Smartly feed* og kjør
   **Run workflow** én gang manuelt for å generere første versjon.
4. Deretter kjører den automatisk hver time.

## Justere terskelen

Terskelen er `MIN_EVENTS` (default `3`). Endre den i
`.github/workflows/update-feed.yml`:

```yaml
env:
  MIN_EVENTS: "3"
```

## Kjøre lokalt

```bash
python3 scripts/process_feed.py
# eller med egne verdier:
MIN_EVENTS=4 OUTPUT_PATH=output/facebook_smartly.csv python3 scripts/process_feed.py
```

Ingen avhengigheter utover Python 3 standardbibliotek.

## Merknader

- **Fortidige arrangement filtreres ikke bort** som standard. Datofeltet er
  norske tekstintervaller (`"6. februar - 11. september"`) som er utrygt å
  tolke automatisk. Si fra om du vil ha datofiltrering — det krever litt
  ekstra parselogikk.
- GitHub kan forsinke planlagte kjøringer med noen minutter ved høy last.
  For en times-feed er det uproblematisk.

## GitHub Pages (valgfri, penere URL)

Slå på Pages for repoet (Settings → Pages, kilde = `main` / rot). Da blir
feeden tilgjengelig på:

```
https://<BRUKER>.github.io/<REPO>/output/facebook_smartly.csv
```
# US-marketing-feed
