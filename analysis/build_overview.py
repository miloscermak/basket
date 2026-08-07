# Vygeneruje web/data/overview.json — velký obraz sezóny 2025/26
# z kompletních enumeračních dat (zápasy, soutěže, haly, rozhodčí, pbp).
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"


def category(db_category):
    """Normalizace kategorie z portálu (taby: muži/Muži/ženy/U13/U11KVAL/žáci…)."""
    c = (db_category or "").lower().replace("kval", "").strip()
    if c in ("muži", "muzi"):
        return "muži"
    if c in ("ženy", "zeny"):
        return "ženy"
    return "mládež"


def youth_age(db_category):
    """U-kategorie pro rozpad mládeže (U10–U19), jinak None."""
    m = re.match(r"u(\d+)", (db_category or "").lower().replace("kval", "").strip())
    return f"U{m.group(1)}" if m else None


def main():
    con = sqlite3.connect(ROOT / "data" / "basket.sqlite", timeout=60)
    con.row_factory = sqlite3.Row
    played = "home_score IS NOT NULL"

    o = {}
    r = con.execute(f"""
        SELECT COUNT(*) n, SUM(home_score+away_score) pts,
               ROUND(AVG(home_score+away_score),1) avg_pts,
               SUM(home_score>away_score)*1.0/COUNT(*) home_win
        FROM matches WHERE {played}""").fetchone()
    o["zapasu"] = r["n"]
    o["bodu_celkem"] = r["pts"]
    o["prumer_bodu"] = r["avg_pts"]
    o["domaci_vyhry_podil"] = round(r["home_win"], 4)
    o["soutezi"] = con.execute("SELECT COUNT(*) FROM competitions").fetchone()[0]
    # sjednocení hráčů se sezónními statistikami (games>0) a hráčů z boxscores
    # (druzí zachytí i minibasket, kde se individuální stat. stránky negenerují,
    # ale hráč v zápase prokazatelně nastoupil) — jinak přijdeme o ~1300 lidí
    o["hracu_se_statistikami"] = con.execute("""
        SELECT COUNT(DISTINCT player_id) FROM (
            SELECT player_id FROM player_group_stats
            UNION
            SELECT player_id FROM boxscores
        )""").fetchone()[0]
    o["hal"] = con.execute(
        f"SELECT COUNT(DISTINCT venue) FROM matches WHERE venue IS NOT NULL AND {played}").fetchone()[0]

    # kategorie (z tabů portálu) + rozpad mládeže po ročnících
    cats, cat_pts, youth = Counter(), Counter(), Counter()
    for row in con.execute(f"""
        SELECT c.category cat, COUNT(*) n, SUM(m.home_score+m.away_score) pts
        FROM matches m JOIN groups g ON m.group_id=g.id
        JOIN competitions c ON g.competition_id=c.id
        WHERE {played} GROUP BY c.id"""):
        cat = category(row["cat"])
        cats[cat] += row["n"]
        cat_pts[cat] += row["pts"] or 0
        ya = youth_age(row["cat"])
        if ya:
            youth[ya] += row["n"]
    o["kategorie"] = {k: {"zapasu": cats[k], "bodu": cat_pts[k]} for k in cats}
    o["mladez_rocniky"] = dict(sorted(youth.items()))

    # oblasti
    o["oblasti"] = [
        dict(row)
        for row in con.execute(f"""
            SELECT c.area, COUNT(*) zapasu FROM matches m
            JOIN groups g ON m.group_id=g.id JOIN competitions c ON g.competition_id=c.id
            WHERE {played} GROUP BY c.area ORDER BY 2 DESC""")
    ]

    # heatmapa den × hodina
    heat = Counter()
    for row in con.execute(f"SELECT date, time FROM matches WHERE {played} AND date IS NOT NULL AND time IS NOT NULL"):
        import datetime
        d = datetime.date.fromisoformat(row["date"])
        hour = int(row["time"].split(":")[0])
        heat[(d.isoweekday(), hour)] += 1
    o["heatmapa"] = [{"den": k[0], "hodina": k[1], "n": v} for k, v in sorted(heat.items())]

    # zápasy po týdnech
    o["tydny"] = [
        dict(row)
        for row in con.execute(f"""
            SELECT strftime('%Y-%W', date) tyden, COUNT(*) n
            FROM matches WHERE {played} AND date IS NOT NULL GROUP BY 1 ORDER BY 1""")
    ]

    # skóre kuriozity
    o["nejvyssi_vyhra"] = [
        dict(row)
        for row in con.execute(f"""
            SELECT m.date, m.home, m.away, m.home_score, m.away_score,
                   ABS(m.home_score-m.away_score) rozdil, c.name soutez
            FROM matches m JOIN groups g ON m.group_id=g.id
            JOIN competitions c ON g.competition_id=c.id
            WHERE {played} ORDER BY rozdil DESC LIMIT 10""")
    ]
    o["nejvic_bodu"] = [
        dict(row)
        for row in con.execute(f"""
            SELECT m.date, m.home, m.away, m.home_score, m.away_score,
                   m.home_score+m.away_score soucet, c.name soutez
            FROM matches m JOIN groups g ON m.group_id=g.id
            JOIN competitions c ON g.competition_id=c.id
            WHERE {played} ORDER BY soucet DESC LIMIT 10""")
    ]
    o["nejtesnejsich_o1"] = con.execute(
        f"SELECT COUNT(*) FROM matches WHERE {played} AND ABS(home_score-away_score)=1").fetchone()[0]

    # domácí výhoda podle úrovně (dospělí) — čím níž, tím větší?
    lvl_case = """
        CASE
            WHEN c.name LIKE '%NBL%' OR c.name LIKE '%ŽBL%' THEN 'profi (NBL/ŽBL)'
            WHEN c.name LIKE '1. liga%' THEN '1. liga'
            WHEN c.name LIKE '2. liga%' THEN '2. liga'
            WHEN c.area > 0 THEN 'kraj/oblast'
            ELSE 'ostatní'
        END"""
    o["domaci_vyhoda_urovne"] = [
        dict(row)
        for row in con.execute(f"""
            SELECT {lvl_case} uroven, COUNT(*) zapasu,
                   ROUND(SUM(m.home_score>m.away_score)*100.0/COUNT(*),1) domaci_pct
            FROM matches m JOIN groups g ON m.group_id=g.id
            JOIN competitions c ON g.competition_id=c.id
            WHERE {played} AND LOWER(c.category) IN ('muži','ženy')
            GROUP BY uroven HAVING zapasu>100 ORDER BY domaci_pct DESC""")
    ]

    # nejvytíženější rozhodčí
    refs = Counter()
    for (r_str,) in con.execute(f"SELECT referees FROM matches WHERE referees IS NOT NULL AND {played}"):
        for name in r_str.split(";"):
            name = name.strip()
            # "Zajistí pořadatel" apod. nejsou jména rozhodčích
            if len(name) > 4 and "pořadatel" not in name.lower() and "zajistí" not in name.lower():
                refs[name] += 1
    o["rozhodci_top"] = [{"jmeno": n, "zapasu": c} for n, c in refs.most_common(15)]
    o["rozhodcich_celkem"] = len(refs)

    # nejvytíženější haly
    o["haly_top"] = [
        dict(row)
        for row in con.execute(f"""
            SELECT venue hala, COUNT(*) zapasu FROM matches
            WHERE venue IS NOT NULL AND {played} GROUP BY venue ORDER BY 2 DESC LIMIT 15""")
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "overview.json").write_text(json.dumps(o, ensure_ascii=False, indent=1))
    print("OK ->", OUT / "overview.json")
    for k in ("zapasu", "bodu_celkem", "prumer_bodu", "domaci_vyhry_podil",
              "hal", "rozhodcich_celkem", "nejtesnejsich_o1"):
        print(k, "=", o[k])
    print("kategorie:", o["kategorie"])


if __name__ == "__main__":
    sys.exit(main())
