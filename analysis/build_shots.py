# Vygeneruje web/data/shots.json — střelecké mapy (hustota střel na půlce
# hřiště po buňkách) a podíl trojek podle úrovně soutěže.
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"

CELL = 2.5  # velikost buňky v procentech hřiště

# skupiny soutěží pro mapy
BUCKETS = [
    ("NBL", "c.id = 5015"),
    ("ŽBL", "c.id = 5033"),
    ("1. liga mužů", "c.name = '1. liga mužů'"),
    ("Mládež (extraligy)", "c.name LIKE 'Extraliga U%'"),
]


def main():
    con = sqlite3.connect(ROOT / "data" / "basket.sqlite", timeout=60)
    con.row_factory = sqlite3.Row
    d = {"cell": CELL, "mapy": {}}

    for label, cond in BUCKETS:
        grid = defaultdict(lambda: [0, 0])  # (xbin, ybin) -> [pokusy, koše]
        rows = con.execute(f"""
            SELECT CASE WHEN s.x>50 THEN 100-s.x ELSE s.x END fx,
                   CASE WHEN s.x>50 THEN 100-s.y ELSE s.y END fy,
                   s.made
            FROM shots s
            JOIN matches m ON m.livestats_id=s.livestats_id
            JOIN groups g ON g.id=m.group_id
            JOIN competitions c ON c.id=g.competition_id
            WHERE {cond} AND s.x IS NOT NULL""")
        total = made = 0
        for r in rows:
            key = (int(r["fx"] // CELL), int(r["fy"] // CELL))
            grid[key][0] += 1
            grid[key][1] += r["made"] or 0
            total += 1
            made += r["made"] or 0
        d["mapy"][label] = {
            "strel": total,
            "usp": round(100 * made / total, 1) if total else 0,
            "cells": [[k[0], k[1], v[0], v[1]] for k, v in sorted(grid.items())],
        }
        print(label, total, "střel")

    # podíl střel za 3 body podle úrovně (z boxscores — pokrývá i soutěže bez map)
    d["trojky_urovne"] = [
        dict(row)
        for row in con.execute("""
            SELECT CASE
                WHEN c.id=5015 THEN 'NBL'
                WHEN c.id=5033 THEN 'ŽBL'
                WHEN c.name LIKE '1. liga%' THEN '1. liga'
                WHEN c.name LIKE '2. liga%' THEN '2. liga'
                WHEN c.area>0 AND LOWER(c.category) IN ('muži','ženy') THEN 'kraj/oblast'
                ELSE NULL END uroven,
                ROUND(100.0*SUM(b.p3a)/(SUM(b.p2a)+SUM(b.p3a)),1) podil_trojek,
                ROUND(100.0*SUM(b.p3m)/SUM(b.p3a),1) uspesnost
            FROM boxscores b
            JOIN matches m ON m.id=b.match_id
            JOIN groups g ON g.id=m.group_id
            JOIN competitions c ON c.id=g.competition_id
            WHERE b.p3a IS NOT NULL AND b.p2a IS NOT NULL
            GROUP BY uroven
            HAVING uroven IS NOT NULL AND podil_trojek IS NOT NULL
            ORDER BY podil_trojek DESC""")
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "shots.json").write_text(json.dumps(d, ensure_ascii=False))
    print("OK -> shots.json | trojky:", d["trojky_urovne"])


if __name__ == "__main__":
    sys.exit(main())
