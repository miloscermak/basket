# Jak se v Česku hrál basketbal — sezóna 2025/26 v datech

Datový projekt mapující **kompletní českou basketbalovou sezónu 2025/26**: každý
soutěžní zápas od Maxa NBL po oblastní přebory minižáků, každý koš, každá hala,
každý rozhodčí. Vznikl jako podklad pro vyhlášení Basketbalisty roku 2026.

## Čísla sezóny

| | |
|---|---|
| Odehraných zápasů | **18 440** |
| Bodů celkem | **2 168 646** |
| Soutěží | 244 (11 oblastí + celostátní) |
| Hráčů a hráček ve statistikách | 22 112 |
| Hal a tělocvičen | 373 |
| Rozhodčích | 651 |
| Play-by-play událostí | 754 tisíc |
| Střel se souřadnicemi | 169 tisíc |
| Kariérních záznamů (od 1998/99) | 256 tisíc sezónních řádků, 79 tisíc osobních rekordů |

## Jak si web prohlédnout

```bash
python3 -m http.server 8763 --directory web
# → http://localhost:8763
```

Web je čisté HTML + CSS + vanilla JavaScript bez závislostí. Data čte
z předpočítaných JSONů ve `web/data/` (jsou součástí repozitáře, web tedy funguje
i bez databáze).

## Odkud jsou data

1. **cz.basketball** — oficiální portál ČBF. Jedna platforma pro celou pyramidu:
   výsledky, rozpisy, box scores, haly, rozhodčí, komisaři, profily hráčů
   s kariérami od sezóny 1998/99. Server-rendered HTML, bez přihlašování.
2. **FIBA LiveStats (Genius Sports)** — u ~1 700 zápasů (NBL, ŽBL, 1. liga,
   mládežnické extraligy) veřejný JSON s play-by-play, střeleckými mapami,
   návštěvností a rozhodčími: `…/data/{matchId}/data.json`, kód ligy `CBFFE`.

Stahování probíhá zdvořile (pauzy mezi requesty, identifikační User-Agent
s kontaktem) a všechny stažené stránky se cachují na disk, takže se nic
nestahuje dvakrát.

## Architektura

```
scraper/   stahování + parsování  →  data/basket.sqlite (není v gitu)
analysis/  SQL/Python analýzy     →  web/data/*.json (v gitu)
web/       statický web           →  čte JSONy
```

### Scraper (`scraper/`)

| Skript | Co dělá |
|---|---|
| `run_pipeline.sh` | spustí celou pipeline po řadě, dá se kdykoli přerušit a znovu pustit |
| `enumerate_matches.py` | indexy soutěží všech oblastí → soutěže, skupiny, zápasy (včetně hal a rozhodčích); NBL/ŽBL se přidávají ručně (nejsou v indexu portálu) |
| `download_details.py` / `parse_details.py` | detaily zápasů → individuální box scores, návštěvnost, ID týmů |
| `download_livestats.py` / `parse_livestats.py` | LiveStats JSONy → play-by-play, střely, týmové součty (body z laviček, největší vedení…) |
| `download_players.py` / `parse_players.py` | profily hráčů → kariéry po sezónách, osobní rekordy |
| `parse_group_stats.py` | sezónní průměry hráčů (věk, pozice) ze stránek soutěží |
| `parse_categories.py` | kategorie soutěží (muži/ženy/U10–U19) z tabů indexu |

### Databáze (`data/basket.sqlite`, ~208 MB)

Hlavní tabulky: `competitions`, `groups`, `matches` (zápasy s halou, rozhodčími,
návštěvností), `boxscores` (výkony hráčů po zápasech), `players`,
`player_seasons` (kariéry), `player_records` (osobní rekordy),
`player_group_stats` (+ pohled `player_comp_stats` bez duplicit), `pbp`
(play-by-play), `shots` (střely se souřadnicemi), `ls_teams`, `ls_meta`.

### Analýzy (`analysis/`)

`build_overview.py` (velký obraz, heatmapa, domácí výhoda), `build_records.py`
(kuriozity, rekordy, lidé sezóny), `build_careers.py` (historické kariéry).
Po jakékoliv změně dat stačí skripty spustit znovu — JSONy se přepíšou.

## Známé limity dat

- **Individuální statistiky** se vedou až od úrovní s elektronickým zápisem;
  v minibasketu bývá jen výsledek a soupisky. Žebříčky výkonů proto počítají jen
  se zápasy, kde součet bodů hráčů sedí na skóre týmu.
- **Návštěvnost** v nižších soutěžích občas obsahuje zjevné nesmysly
  (analýzy používají strop 8 000 diváků).
- **Play-by-play a střely** existují jen u zápasů s FIBA LiveStats (~1 700).
- **Věk hráčů** je aktuální věk z portálu, ne věk v den zápasu.
- Portál eviduje statistiky od 1998/99, plné box scores zhruba od 2005,
  nižší soutěže až od nástupu elektronického zápisu (~2023).

## Co může doplnit federace

Web má připravené prázdné sekce pro: **demografii** (registrace hráčů z Lerisu
podle věku/pohlaví/kraje), **přestupy** (migrační mapa mezi kluby) a **rozhodčí**
(licence, věková struktura, vytížení). Kompletní wishlist s odůvodněním je
v [PRUZKUM.md](PRUZKUM.md), sekce 3.

## Obnova dat

Databáze i cache nejsou v gitu. Kompletní znovupostavení:

```bash
python3 -m venv .venv && .venv/bin/pip install requests beautifulsoup4 lxml
nohup caffeinate -i scraper/run_pipeline.sh > data/pipeline.log 2>&1 &
```

Trvá to několik hodin (18 tisíc detailů zápasů + 23 tisíc profilů hráčů při
zdvořilém tempu). Cache se využije, pokud existuje.
