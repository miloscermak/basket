# Vygeneruje web/data/search.json — kompaktní index všech hráčů
# pro vyhledávání přímo v prohlížeči.
# Formát řádku: [jméno, věk, týmy, zápasy 25/26, body/zápas, soutěží,
#                první sezóna, sezón celkem, kariérní bodové maximum]
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"


def main():
    con = sqlite3.connect(ROOT / "data" / "basket.sqlite", timeout=60)
    con.row_factory = sqlite3.Row

    rows = con.execute("""
        SELECT s.player_id, s.name,
               MAX(s.age) age,
               GROUP_CONCAT(DISTINCT s.team) teams,
               SUM(s.games) games,
               ROUND(SUM(s.games*s.pts_avg)/SUM(s.games), 1) ppg,
               COUNT(*) comps,
               (SELECT MIN(ps.season) FROM player_seasons ps WHERE ps.player_id=s.player_id) first_season,
               (SELECT COUNT(DISTINCT ps.season) FROM player_seasons ps WHERE ps.player_id=s.player_id) seasons,
               (SELECT CAST(r.value AS INTEGER) FROM player_records r
                WHERE r.player_id=s.player_id AND r.stat='Body') rec_pts
        FROM player_comp_stats s
        WHERE s.games > 0
        GROUP BY s.player_id
        ORDER BY s.name""").fetchall()

    index = [
        [r["name"], r["age"], r["teams"], r["games"], r["ppg"], r["comps"],
         r["first_season"], r["seasons"], r["rec_pts"]]
        for r in rows
    ]
    znamych = {r["player_id"] for r in rows}

    # hráči, co mají jen boxscores (bez sezónní stat. stránky) — typicky
    # minibasket, kde se individuální statistiky negenerují; bez nich by
    # web tvrdil "23 408 hledatelných lidí" a lhal by o 1300 z nich
    navic = con.execute("""
        SELECT b.player_id, b.name,
               GROUP_CONCAT(DISTINCT CASE b.team_side WHEN 1 THEN m.home ELSE m.away END) teams,
               COUNT(DISTINCT b.match_id) games,
               ROUND(AVG(b.pts), 1) ppg,
               COUNT(DISTINCT c.id) comps,
               (SELECT MIN(ps.season) FROM player_seasons ps WHERE ps.player_id=b.player_id) first_season,
               (SELECT COUNT(DISTINCT ps.season) FROM player_seasons ps WHERE ps.player_id=b.player_id) seasons,
               (SELECT CAST(r.value AS INTEGER) FROM player_records r
                WHERE r.player_id=b.player_id AND r.stat='Body') rec_pts
        FROM boxscores b
        JOIN matches m ON m.id = b.match_id
        JOIN groups g ON g.id = m.group_id
        JOIN competitions c ON c.id = g.competition_id
        GROUP BY b.player_id
        ORDER BY b.name""").fetchall()

    for r in navic:
        if r["player_id"] in znamych:
            continue
        index.append([r["name"], None, r["teams"], r["games"], r["ppg"], r["comps"],
                      r["first_season"], r["seasons"], r["rec_pts"]])
    index.sort(key=lambda row: row[0])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "search.json").write_text(json.dumps(index, ensure_ascii=False))
    size = (OUT / "search.json").stat().st_size
    print(f"OK -> search.json: {len(index)} hráčů, {size/1e6:.1f} MB")


if __name__ == "__main__":
    sys.exit(main())
