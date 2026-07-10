# Basket — datová analýza české basketbalové sezóny 2025/26

Projekt pro vyhlášení Basketbalisty roku (srpen 2026, Miloš moderuje). Cíl: web
ukazující maximum z veřejných dat o celé české basketbalové pyramidě + připravený
na data od federace (ČBF).

## Struktura

- `scraper/` — stahování a parsování dat z cz.basketball a FIBA LiveStats
- `analysis/` — generátory JSONů pro web (čtou SQLite, píšou do `web/data/`)
- `web/` — statický web (čisté HTML + CSS + vanilla JS, žádné závislosti)
- `data/` — NENÍ v gitu: `basket.sqlite` (208 MB) + `raw/` cache stažených stránek (1,4 GB)
- `PRUZKUM.md` — výchozí průzkum zdrojů dat a nápadů na analýzy

## Pipeline (vše idempotentní, navazuje na přerušenou práci)

`scraper/run_pipeline.sh` spustí vše po řadě. Jednotlivé kroky:

1. `enumerate_matches.py` — projde indexy soutěží (area 0–14) + ručně přidané
   NBL/ŽBL (EXTRA_GROUPS), stáhne stránky skupin, vytěží zápasy
2. `download_details.py` → `parse_details.py` — detaily zápasů → boxscores
3. `download_livestats.py` → `parse_livestats.py` — JSONy Genius Sports → pbp, střely
4. `download_players.py` → `parse_players.py` — profily hráčů → kariéry, rekordy
5. `parse_group_stats.py`, `parse_categories.py` — sezónní statistiky a kategorie
   z už cachovaných stránek
6. `analysis/build_*.py` — přegenerování JSONů pro web (přehled v README)
7. `analysis/bundle_data.py` — VŽDY nakonec: balí JSONy do `web/data.js`
   (web čte data odtud, ať funguje i z file://; `data.js` needitovat ručně)

Stahování běží slušně (0,4 s pauza, UA s kontaktem). Dlouhé běhy spouštět přes
`nohup caffeinate -i …`, jinak je uspání Macu zabije.

## Zdroje dat a jejich záludnosti

- **cz.basketball** — server-rendered HTML, bez autentizace. Zápas `/zapas/{id}`,
  soutěž `/soutez/{sid}?p={gid}`, hráč `/hrac/{id}`.
- **NBL (5015) a ŽBL (5033) NEJSOU v indexu** `/soutez?area=0` — přidávají se ručně
  přes EXTRA_GROUPS v enumerate_matches.py. Při nové sezóně aktualizovat ID fází!
- **FIBA LiveStats**: `fibalivestats.dcd.shared.geniussports.com/data/{id}/data.json`,
  kód ligy CBFFE. Některé záznamy vrací 403/404 (zablokované) — přeskakují se.
- **Stránka skupiny obsahuje statistiky CELÉ soutěže**, ne jen skupiny → tabulka
  `player_group_stats` má duplicity; VŽDY agregovat přes pohled `player_comp_stats`
  (MAX(games) na hráče a soutěž).
- **Návštěvnost je občas nesmysl** (skorotéři zapisují i miliardu) — v analýzách
  strop 8000.
- **Prodloužení** v pbp: `period_type='OVERTIME'` a `period` se počítá znovu od 1
  (metadata `period` zůstávají 4).
- **Boxscore není vždy kompletní** (hlavně minibasket) — individuální žebříčky
  filtrovat přes temp tabulku `_complete_box` (součet bodů hráčů == skóre týmu).
- **Kategorie soutěží** (muži/ženy/U10–U19) jsou z tabů indexových stránek;
  enumerate je NESMÍ přepsat (upsert zachovává sloupec category).
- **Ženská příjmení** se slučují s mužskými přes kandidáty (Nováková→Novák,
  Svobodová→Svoboda, Novotná→Novotný) — viz make_normalizer v build_names.py;
  prosté oříznutí „-ová" nestačí.
- **Souřadnice střel** pokrývají celé hřiště (x 0–100 délka, y 0–100 šířka);
  na jednu polovinu se překládají zrcadlením: x>50 → (100−x, 100−y). Koš je
  ~5,6 jednotky od čáry.
- **Clutch definice**: poslední 2 min 4. čtvrtiny nebo prodloužení, |lead| ≤ 5.
- V pbp/shots/ls_teams jsou hráči jen jménem („D. Elich"), NE portálovým ID —
  napojení na tabulku players jde jen přes jméno a tým, opatrně na shody jmen.

## Nasazení

- GitHub: https://github.com/miloscermak/basket
- Netlify: statický deploy složky `web/` (netlify.toml), bez build kroku.

## Konvence

- Kód komentovat česky, commity anglicky, komunikace česky.
- `data/` se do gitu nikdy nepřidává; JSONy ve `web/data/` ANO (web je bez nich prázdný).
- Web: žádné frameworky ani CDN — musí fungovat offline z lokálního serveru.
- Náhled webu: `.claude/launch.json` → server „web" (python http.server na :8763).

## Co čeká na data od federace (sekce webu jsou připravené)

Registrace hráčů z Lerisu (demografie), přestupy, databáze rozhodčích,
disciplinárka — detailní wishlist v PRUZKUM.md, sekce 3.
