# Vygeneruje web/data/pbp.json — clutch žebříček a anatomii zápasu
# z play-by-play dat (zápasy s FIBA LiveStats: NBL, ŽBL, 1. liga, extraligy).
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"

# koncovka = poslední 2 minuty 4. čtvrtiny nebo celé prodloužení,
# rozdíl skóre max 5 bodů
CLUTCH = """
    ((period=4 AND period_type='REGULAR' AND gt<='02:00') OR period_type='OVERTIME')
    AND ABS(lead) <= 5 AND success=1
    AND action_type IN ('2pt','3pt','freethrow')
"""
PTS = "CASE action_type WHEN '3pt' THEN 3 WHEN '2pt' THEN 2 ELSE 1 END"


def main():
    con = sqlite3.connect(ROOT / "data" / "basket.sqlite", timeout=60)
    con.row_factory = sqlite3.Row
    d = {}

    # clutch střelci: body v koncovkách vyrovnaných zápasů
    d["clutch"] = [
        dict(row)
        for row in con.execute(f"""
            SELECT p.player jmeno, t.name tym, SUM({PTS}) bodu,
                   COUNT(DISTINCT p.livestats_id) zapasu,
                   (SELECT c.name FROM matches m
                    JOIN groups g ON g.id=m.group_id
                    JOIN competitions c ON c.id=g.competition_id
                    WHERE m.livestats_id=p.livestats_id) soutez
            FROM pbp p
            JOIN ls_teams t ON t.livestats_id=p.livestats_id AND t.tno=p.tno
            WHERE {CLUTCH} AND p.player IS NOT NULL AND p.player != ''
            GROUP BY p.player, t.name
            ORDER BY bodu DESC LIMIT 15""")
    ]

    # kolik vyrovnaných koncovek vůbec bylo
    d["clutch_zapasu"] = con.execute(
        f"SELECT COUNT(DISTINCT livestats_id) FROM pbp WHERE {CLUTCH}"
    ).fetchone()[0]

    # anatomie zápasu: body v každé minutě (průměr na zápas, obě družstva dohromady)
    n_games = con.execute(
        "SELECT COUNT(DISTINCT livestats_id) FROM pbp WHERE period_type='REGULAR'"
    ).fetchone()[0]
    rows = con.execute(f"""
        SELECT (period-1)*10 + MIN(9, 10 - CAST(substr(gt,1,2) AS INTEGER)) minuta,
               SUM({PTS}) bodu
        FROM pbp
        WHERE period_type='REGULAR' AND success=1
          AND action_type IN ('2pt','3pt','freethrow')
        GROUP BY minuta ORDER BY minuta""").fetchall()
    d["anatomie"] = [
        {"minuta": r["minuta"] + 1, "bodu_prumer": round(r["bodu"] / n_games, 2)}
        for r in rows if 0 <= r["minuta"] < 40
    ]
    d["anatomie_zapasu"] = n_games

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pbp.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print("OK -> pbp.json | clutch hráčů:", len(d["clutch"]),
          "| koncovek:", d["clutch_zapasu"], "| zápasů pro anatomii:", n_games)
    print("top clutch:", dict(d["clutch"][0]) if d["clutch"] else None)


if __name__ == "__main__":
    sys.exit(main())
