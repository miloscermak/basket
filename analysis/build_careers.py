# Vygeneruje web/data/careers.json — historické kariéry z profilů hráčů
# (portál eviduje sezóny od 1998/99).
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"


def main():
    con = sqlite3.connect(ROOT / "data" / "basket.sqlite", timeout=60)
    con.row_factory = sqlite3.Row
    c = {}

    # hráči aktivní letos (mají sezónu 2025/26)
    con.execute("DROP TABLE IF EXISTS _active")
    con.execute("""
        CREATE TEMP TABLE _active AS
        SELECT DISTINCT player_id FROM player_seasons WHERE season='2025/26'
    """)

    # nejdelší kariéry stále aktivních (od první sezóny na portálu)
    c["nejdelsi_kariery"] = [
        dict(row)
        for row in con.execute("""
            SELECT p.name jmeno, MIN(s.season) prvni, COUNT(DISTINCT s.season) sezon,
                   SUM(s.games) zapasu
            FROM player_seasons s
            JOIN _active a ON a.player_id=s.player_id
            JOIN players p ON p.id=s.player_id
            GROUP BY s.player_id
            HAVING sezon >= 20
            ORDER BY sezon DESC, prvni LIMIT 15""")
    ]

    # nejvíc zápasů v evidované historii (kdokoliv, i neaktivní)
    c["nejvic_zapasu_historie"] = [
        dict(row)
        for row in con.execute("""
            SELECT p.name jmeno, SUM(s.games) zapasu, COUNT(DISTINCT s.season) sezon,
                   MIN(s.season) prvni, MAX(s.season) posledni,
                   EXISTS(SELECT 1 FROM _active a WHERE a.player_id=s.player_id) aktivni
            FROM player_seasons s JOIN players p ON p.id=s.player_id
            GROUP BY s.player_id
            ORDER BY zapasu DESC LIMIT 15""")
    ]

    # veteráni, kteří si LETOS vylepšili osobní bodový rekord
    c["rekordy_letos"] = [
        dict(row)
        for row in con.execute("""
            SELECT p.name jmeno, r.stat, r.value hodnota, r.date datum,
                   (SELECT MAX(age) FROM player_comp_stats pcs WHERE pcs.player_id=r.player_id) vek,
                   (SELECT COUNT(DISTINCT season) FROM player_seasons ps WHERE ps.player_id=r.player_id) sezon
            FROM player_records r JOIN players p ON p.id=r.player_id
            WHERE r.season='2025/26' AND r.stat LIKE '%body%' AND r.stat NOT LIKE '_B%'
              AND r.value >= 15
              AND (SELECT COUNT(DISTINCT season) FROM player_seasons ps
                   WHERE ps.player_id=r.player_id AND ps.season < '2015/16') > 0
            ORDER BY vek DESC LIMIT 12""")
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "careers.json").write_text(json.dumps(c, ensure_ascii=False, indent=1))
    print("OK ->", OUT / "careers.json")
    for k, v in c.items():
        print(k, "=", len(v))
        if v:
            print("  napr.:", dict(v[0]))


if __name__ == "__main__":
    sys.exit(main())
