# Průzkum: data o českém basketbalu, sezóna 2025/26

*Vzniklo 3. 7. 2026 jako první krok projektu „co nejzajímavější datová analýza uplynulé basketbalové sezóny v Česku".*

## TL;DR — hlavní zjištění

1. **Celý český basketbal běží na jednom veřejném systému.** Portál cz.basketball (a jeho klony nbl.basketball, zbl.basketball) pokrývá všechno od Maxa NBL po oblastní přebor minižáků U10. Za sezónu 2025/26 je v něm **18 331 zápasů** ve zhruba **750–800 skupinách soutěží** a **321 klubech**. Stránky jsou obyčejné HTML bez přihlašování — snadno strojově čitelné.
2. **Každý moderní zápas má navíc veřejný JSON s kompletními daty.** Federace používá FIBA LiveStats (Genius Sports, kód ligy `CBFFE`) a endpoint `https://fibalivestats.dcd.shared.geniussports.com/data/{matchId}/data.json` vrací bez autentizace: box score všech hráčů, **kompletní play-by-play** (~600 akcí na zápas), **střelecké mapy se souřadnicemi**, návštěvnost, rozhodčí, průběh vedení. Funguje pro NBL, ŽBL, 1. ligu i mládežnické extraligy.
3. **Historie sahá do sezóny 1998/99**, box scores spolehlivě od ~2005 (národní soutěže), play-by-play od ~2017, elektronický zápis v nižších soutěžích od ~2023.
4. Co veřejně **není**: souhrnná registrační data (počty hráčů podle věku/kraje), přestupy, disciplinárka, kompletní data rozhodčích, syrová data NBN23 z nižších soutěží. To všechno **federace má** ve svých systémech (Leris, NBN23/Swish) — viz wishlist na konci.

---

## 1. Co je veřejně k dispozici

### Centrální portál cz.basketball — páteř všeho

| Data | URL vzor | Poznámka |
|---|---|---|
| Všechny zápasy sezóny | `/zapasy?y=2025&d_od=2025-09-01&d_do=2026-06-30` | jeden request = 18 331 zápasů všech úrovní |
| Přehled soutěží | `/soutez?y=2025&area={0–14}` | `area 0` = celostátní, 1 = Praha, 2 = Stř. Čechy, 7 = J. Morava… |
| Detail soutěže | `/soutez/{id}?p={skupina}` | tabulka, rozpis, výsledky, statistiky hráčů, hodnocení rozhodčích |
| Detail zápasu | `/zapas/{id}` | box score, čtvrtiny, rozhodčí jménem, hala, **diváci** |
| Hráč | `/hrac/{id}` | kariéra po sezónách 20+ let zpět, klub, národnost, ročník |
| Kluby | `/kluby` | ~321 klubů s adresami |

**Granularita podle úrovně** (ověřeno na živých stránkách):
- **NBL, ŽBL, 1. liga:** plný FIBA box score (minuty, doskoky útočné/obranné, asistence, bloky, +/-, efektivita…) + LiveStats JSON s play-by-play a shot charts.
- **2. liga a krajské přebory:** zjednodušený zápis — dvojky/trojky/šestky proměněné, fauly, body na hráče; rozhodčí, hala, diváci, čtvrtiny.
- **Minižactvo (U12 a níž):** čtvrtiny, kompletní soupisky s čísly dresů, ale individuální statistiky se nevedou.

### Profesionální ligy — specializované weby

- **nbl.basketball** (Maxa NBL, dříve Kooperativa NBL): statistické centrum s lídry, TOP výkony, srovnávače, **tabulka návštěvnosti po zápasech** (`/navstevnost`), profily sezón od 1998/99. Fáze 2025/26: základní část `p1=9361`, nadstavba 9362/9363, předkolo 9365, play-off 9366, baráž 9367.
- **zbl.basketball** (Chance ŽBL): identická platforma, 10 týmů, sezóny od 1998/99.
- **Český pohár:** muži `cz.basketball/soutez/5016` (finále: Nymburk 87:81 Pardubice, Opava 21. 2. 2026), ženy `soutez/5036` (vítěz SBŠ Ostrava).

### Základní fakta sezóny 2025/26 (ověřená)

- **NBL:** mistr **ERA Basketball Nymburk — 21. titul**, finále 4:3 proti BK KVIS Pardubice (7. zápas 91:74, MVP Ondřej Sehnal). Historická tečka: Nymburk se stěhuje do Prahy jako SK Slavia Praha ERA NBK — **konec nymburské éry je hotový narativ pro celou analýzu**.
- **ŽBL:** mistryně **ZVVZ USK Praha** (3:0 na Žabiny Brno). USK zároveň obhajoval titul v Eurolize žen.
- **Evropa:** Nymburk v Lize mistrů, Opava ve FIBA Europe Cup, USK Praha v Eurolize žen, Žabiny v EuroCupu žen.
- **Reprezentace:** muži na EuroBasketu 2025 (bez zraněného Satoranského), ženy spolupořádaly EuroBasket 2025 (skupina v Brně).
- **Češi v zahraničí:** Vít Krejčí — v únoru 2026 vytrejdován z Atlanty do Portlandu (kariérní maximum 28 bodů proti Clippers). Data: `nba_api` (ID 1630249), basketball-reference (`krejcvi01`). Češi v NCAA: seznam na RealGM.

### Třetí strany

| Zdroj | K čemu | Přístup |
|---|---|---|
| RealGM | pokročilé statistiky NBL (per-36, advanced), seznamy Čechů v NBA/NCAA | čisté HTML tabulky |
| eurobasket.com | přestupy, cizinci v lize, „Czechs Abroad", týdenní ocenění | jen ke čtení/citaci, scraping nevhodný |
| Flashscore/Livesport (česká firma!) | výsledky vč. archivu, ŽBL, 1. liga žen | neveřejný feed, ToS zakazuje scraping |
| OddsPortal / BetExplorer | **archiv kurzů NBL 2025/26** → analýza největších překvapení | HTML, ToS šedá zóna; oficiálně BetsAPI (placené) |
| Rejstřík sportu (NSA) | počty registrovaných sportovců a organizací podle sportu | veřejný dashboard s exportem, není v data.gov.cz |
| tvcom.cz | video archiv zápasů NBL, ŽBL, poháru | streamy |
| Wikipedia/Wikidata | metadata (kariéry, rodiště, výšky) | SPARQL, ale mělké |

### Hotové nástroje

- `benhur07b/fiba-livestats-scraper` (GitHub), Kaggle notebook na FIBA LiveStats, `euroleague-api` (PyPI), `nba_api`. **Žádný český basketbalový scraper neexistuje — greenfield.**

---

## 2. Nápady na analýzy a fun fakty

### Velký obraz („mapa českého basketbalu")
- **Kolik košů padlo v Česku za sezónu?** 18 331 zápasů × ~140 bodů → řádově 2,5 milionu bodů. Spočítat přesně, rozpadnout po soutěžích, krajích, věkových kategoriích. Skvělý úvodní fun fakt.
- **Basketbalová mapa ČR:** 321 klubů na mapě, zápasy na obyvatele po okresech, „basketbalové pouště" vs. bašty (Nymburk, Opava, Pardubice…). Doplnit počty registrovaných z Rejstříku sportu.
- **Kdy se v Česku hraje basket:** heatmapa dnů a časů všech 18 tisíc zápasů (sobotní ráno mládeže vs. páteční večery NBL).
- **Kolik kilometrů týmy najezdily** — z rozpisů a adres hal spočítat cestování; kdo měl nejkrutější výjezdy.

### Kuriozity a rekordy napříč pyramidou
- **Nejvyšší výhra sezóny** (mládežnické 150:10?), nejtěsnější zápasy, nejvíc prodloužení, největší střelecký výkon jednotlivce v celé ČR.
- **„Železní muži a ženy":** kdo odehrál nejvíc zápasů napříč soutěžemi (dospělí + mládež + více týmů klubu současně)? Ve 2. lize hrají patnáctiletí i padesátníci — najít nejstaršího a nejmladšího aktivního hráče, největší věkový rozdíl na hřišti.
- **Nejdelší kariéry:** hráčské profily sahají 20+ let zpět — kdo hraje nepřetržitě od roku 2005? Kolik hráčů prošlo 5+ kluby?
- **Jména:** nejčastější příjmení českého basketbalu; rodinné klany (stejné příjmení ve stejném týmu = sourozenci/otcové a synové).

### Analytika z play-by-play a shot charts (NBL, ŽBL, 1. liga)
- **Clutch žebříček:** kdo skóroval v posledních 2 minutách vyrovnaných zápasů; kdo naopak v koncovkách mizí.
- **Největší obraty sezóny** (z `leaddata`: největší ztracené vedení), zápas s nejvíce změnami vedení, největší šňůry.
- **Střelecké mapy:** odkud se v Česku střílí vs. NBA trendy — dorazila „trojková revoluce" i do 1. ligy? Mapa oblíbených míst jednotlivých střelců.
- **Anatomie zápasu:** průměrný průběh — kdy padá nejvíc bodů, jak vypadá „garbage time", rozdíl tempa mužů a žen.
- **Domácí výhoda napříč úrovněmi:** je větší v krajském přeboru než v NBL? (Teorie: menší haly, známější prostředí, rozhodčí.) Unikátní analýza, kterou z dat jde udělat jen díky kompletní pyramidě.

### Rozhodčí (opatrně, ale zajímavě)
- Kdo odpískal nejvíc zápasů, nejvytíženější dvojice, kolik rozhodčích Česko vlastně má a jak stárnou.
- Fauly doma vs. venku podle rozhodčích — čistě popisně, bez obviňování.

### Ekonomika pozornosti
- **Návštěvnost:** celková návštěva NBL, nejvěrnější publikum, návštěvnost play-off vs. základní část, poslední sezóna Nymburka v Nymburce — chodili se lidi loučit?
- **Upsety podle kurzů:** největší překvapení sezóny podle sázkových kurzů (OddsPortal archiv).

### Příběhy
- **Konec dynastie:** 21 titulů Nymburka v datech — dominance v číslech (série výher, průměrné rozdíly skóre za 20 let) před stěhováním do Prahy. Vlajkový narativ celého projektu.
- **Pipeline talentů:** kolik hráčů z extraligy U19 se do 3 let objeví v NBL? Kde se ztrácejí? (Data na to jsou — hráčské profily propojují mládež a dospělé.)
- **Ženský basket na vzestupu:** USK Praha jako evropský hegemon vs. domácí liga, kterou vyhrává 3:0.

---

## 3. Co veřejně není, ale federace to má (wishlist pro ČBF)

1. **Registrační data z Lerisu:** počty licencovaných hráčů podle roku narození, pohlaví a kraje, ideálně časová řada 10+ let. → demografie českého basketbalu, kde mizí teenageři, covid efekt. (Veřejně jen údaj „324 členských subjektů".)
2. **Přestupy a hostování:** kompletní log pohybů hráčů → síťová analýza „basketbalové migrace" mezi kluby a kraji.
3. **Syrová data NBN23/Swish** z nižších soutěží (elektronický zápis) — eventy nad rámec toho, co portál zobrazuje.
4. **Databáze rozhodčích:** licence, věk, odpískané zápasy, hodnocení komisařů → příběh o (ne)dostatku rozhodčích.
5. **Disciplinární řízení:** technické chyby, tresty → „nejvyhrocenější soutěž Česka".
6. **Trenérské licence:** kolik trenérů, jaké kvalifikace, věková struktura.
7. **Historická návštěvnost** ŽBL a nižších soutěží (na portálu je jen u části zápasů).
8. **Ekonomika:** rozpočty klubů NBL z licenčního řízení (asi citlivé, ale i agregáty by byly zajímavé).

---

## 4. Doporučený postup projektu

1. **Scraper** (Python): projít `/zapasy?y=2025` → stáhnout HTML detaily zápasů + LiveStats `data.json` tam, kde existuje → uložit do SQLite. Odhad: ~18 tisíc HTML stránek + ~2–3 tisíce JSONů, jeden večer běhu se slušným rate-limitem.
2. **Datový model:** zápasy, týmy, hráči (stabilní numerická ID portálu), soutěže, výkony hráčů, pbp eventy, střely, rozhodčí.
3. **Analýzy** dle sekce 2 — začít velkým obrazem (funguje i bez pbp), pak jít do hloubky NBL.
4. **Výstup:** interaktivní webová prezentace (HTML + CSS + vanilla JS, grafy např. přes lehkou knihovnu) — „Česká basketbalová sezóna 2025/26 v datech".

**Etika scrapingu:** federační portál je veřejný a bez ToS proti scrapingu, ale poběžíme slušně (pauzy mezi requesty, cache). Kurzové weby a Flashscore scraping zakazují — tam jen ručně/citace, nebo data vyžádat.
