# Vygeneruje web/data/records.json — kuriozity, rekordy a lidé sezóny 2025/26.
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"


def main():
    con = sqlite3.connect(ROOT / "data" / "basket.sqlite", timeout=60)
    con.row_factory = sqlite3.Row
    r = {}

    # zápasy s kompletním zápisem (součet bodů hráčů sedí na skóre) — jen v nich
    # věříme individuálním výkonům
    con.execute("DROP TABLE IF EXISTS _complete_box")
    con.execute("""
        CREATE TEMP TABLE _complete_box AS
        SELECT b.match_id, b.team_side
        FROM boxscores b
        JOIN matches m ON m.id=b.match_id
        GROUP BY b.match_id, b.team_side
        HAVING SUM(b.pts) = CASE b.team_side WHEN 1 THEN m.home_score ELSE m.away_score END
    """)

    # nejvyšší individuální výkony sezóny (jen kompletní zápisy)
    r["top_vykony"] = [
        dict(row)
        for row in con.execute("""
            SELECT b.name jmeno, b.pts bodu, m.date datum, m.home domaci, m.away hoste,
                   c.name soutez, c.category kategorie
            FROM boxscores b
            JOIN _complete_box cb ON cb.match_id=b.match_id AND cb.team_side=b.team_side
            JOIN matches m ON m.id=b.match_id
            JOIN groups g ON g.id=m.group_id JOIN competitions c ON c.id=g.competition_id
            ORDER BY b.pts DESC LIMIT 15""")
    ]

    # nejvíc trojek v jednom zápase
    r["trojky_zapas"] = [
        dict(row)
        for row in con.execute("""
            SELECT b.name jmeno, b.p3m trojek, m.date datum, m.home domaci, m.away hoste, c.name soutez
            FROM boxscores b
            JOIN _complete_box cb ON cb.match_id=b.match_id AND cb.team_side=b.team_side
            JOIN matches m ON m.id=b.match_id
            JOIN groups g ON g.id=m.group_id JOIN competitions c ON c.id=g.competition_id
            WHERE b.p3m IS NOT NULL ORDER BY b.p3m DESC LIMIT 10""")
    ]

    # nejstarší hráči a hráčky (agregát přes soutěže)
    r["nejstarsi"] = [
        dict(row)
        for row in con.execute("""
            SELECT name jmeno, MAX(age) vek, team tym, SUM(games) zapasu,
                   GROUP_CONCAT(DISTINCT competition) souteze
            FROM player_comp_stats GROUP BY player_id
            HAVING vek >= 58 AND zapasu >= 5 ORDER BY vek DESC LIMIT 12""")
    ]

    # železní muži a ženy — nejvíc zápasů napříč soutěžemi
    r["zelezni"] = [
        dict(row)
        for row in con.execute("""
            SELECT name jmeno, MAX(age) vek, SUM(games) zapasu, COUNT(*) soutezi,
                   GROUP_CONCAT(DISTINCT team) tymy
            FROM player_comp_stats GROUP BY player_id
            ORDER BY zapasu DESC LIMIT 12""")
    ]

    # největší obraty (tým vedl o N bodů a prohrál)
    r["obraty"] = [
        dict(row)
        for row in con.execute("""
            SELECT t.name tym, t.biggest_lead vedeni, m.date datum,
                   m.home domaci, m.home_score, m.away hoste, m.away_score, c.name soutez
            FROM ls_teams t
            JOIN matches m ON m.livestats_id=t.livestats_id
            JOIN groups g ON g.id=m.group_id JOIN competitions c ON c.id=g.competition_id
            WHERE (t.tno=1 AND m.home_score<m.away_score)
               OR (t.tno=2 AND m.away_score<m.home_score)
            ORDER BY t.biggest_lead DESC LIMIT 8""")
    ]

    # prodloužení
    r["prodlouzeni"] = [
        dict(row)
        for row in con.execute("""
            SELECT DISTINCT m.date datum, m.home domaci, m.home_score, m.away hoste,
                   m.away_score, c.name soutez, MAX(p.period) ot_period
            FROM pbp p JOIN matches m ON m.livestats_id=p.livestats_id
            JOIN groups g ON g.id=m.group_id JOIN competitions c ON c.id=g.competition_id
            WHERE p.period_type='OVERTIME'
            GROUP BY p.livestats_id ORDER BY ot_period DESC, m.date""")
    ]

    # králové smečí (jen soutěže s LiveStats)
    r["smece"] = [
        dict(row)
        for row in con.execute("""
            SELECT player jmeno, COUNT(*) smeci FROM shots
            WHERE sub_type='dunk' AND made=1 GROUP BY player
            ORDER BY 2 DESC LIMIT 10""")
    ]

    # nejdelší šňůry výher (kterýkoli tým, kterákoli soutěž)
    results = defaultdict(list)
    for row in con.execute("""
        SELECT date, home, away, home_score, away_score FROM matches
        WHERE home_score IS NOT NULL AND date IS NOT NULL
          AND home_score != away_score ORDER BY date"""):
        results[row["home"]].append((row["date"], row["home_score"] > row["away_score"]))
        results[row["away"]].append((row["date"], row["away_score"] > row["home_score"]))
    streaks = []
    for team, games in results.items():
        best = cur = 0
        start = best_start = best_end = None
        for date, won in games:
            if won:
                cur += 1
                start = start or date
                if cur > best:
                    best, best_start, best_end = cur, start, date
            else:
                cur, start = 0, None
        if best >= 15:
            streaks.append({"tym": team, "vyher": best, "od": best_start, "do": best_end,
                            "zapasu_celkem": len(games)})
    r["snury"] = sorted(streaks, key=lambda s: -s["vyher"])[:12]

    # návštěvnost — top zápasy
    r["navstevnost_top"] = [
        dict(row)
        for row in con.execute("""
            SELECT m.date datum, m.home domaci, m.away hoste, m.home_score, m.away_score,
                   m.attendance divaku, c.name soutez
            FROM matches m JOIN groups g ON g.id=m.group_id
            JOIN competitions c ON c.id=g.competition_id
            WHERE m.attendance BETWEEN 1 AND 8000 ORDER BY m.attendance DESC LIMIT 10""")
    ]
    # strop 8000: skorotéři v nižších soutěžích občas zapíšou nesmysl (i miliardu)
    row = con.execute(
        "SELECT SUM(attendance) s, COUNT(*) n FROM matches WHERE attendance BETWEEN 1 AND 8000"
    ).fetchone()
    r["navstevnost_celkem"] = {"divaku": row["s"], "zapasu": row["n"]}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "records.json").write_text(json.dumps(r, ensure_ascii=False, indent=1))
    print("OK ->", OUT / "records.json")
    for k, v in r.items():
        print(k, "=", len(v) if isinstance(v, list) else v)


if __name__ == "__main__":
    sys.exit(main())
