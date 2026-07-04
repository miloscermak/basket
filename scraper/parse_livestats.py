# Krok 8: z cachovaných LiveStats JSONů vytěží play-by-play, střelecké mapy,
# týmové součty a návštěvnost do databáze.
import gzip
import json
import sys

import db
from common import RAW

SCHEMA = """
DROP TABLE IF EXISTS pbp;
CREATE TABLE pbp (
    livestats_id INTEGER,
    action_number INTEGER,
    period INTEGER,
    period_type TEXT,
    gt TEXT,                    -- herní čas v periodě (mm:ss, odpočítává se)
    tno INTEGER,                -- 1 = domácí, 2 = hosté, 0 = zápas
    player TEXT,
    shirt TEXT,
    action_type TEXT,
    sub_type TEXT,
    success INTEGER,
    s1 INTEGER, s2 INTEGER,     -- průběžné skóre
    lead INTEGER
);
DROP TABLE IF EXISTS shots;
CREATE TABLE shots (
    livestats_id INTEGER,
    tno INTEGER,
    player TEXT,
    shirt TEXT,
    x REAL, y REAL,             -- souřadnice na hřišti (0-100)
    made INTEGER,
    period INTEGER,
    action_type TEXT,           -- 2pt / 3pt
    sub_type TEXT               -- layup, dunk, jumpshot...
);
DROP TABLE IF EXISTS ls_teams;
CREATE TABLE ls_teams (
    livestats_id INTEGER,
    tno INTEGER,
    name TEXT,
    code TEXT,
    pts INTEGER,
    pts_paint INTEGER,
    pts_fastbreak INTEGER,
    pts_second_chance INTEGER,
    pts_from_turnovers INTEGER,
    pts_bench INTEGER,
    biggest_lead INTEGER,
    biggest_run INTEGER,
    time_leading REAL,
    PRIMARY KEY (livestats_id, tno)
);
DROP TABLE IF EXISTS ls_meta;
CREATE TABLE ls_meta (
    livestats_id INTEGER PRIMARY KEY,
    attendance INTEGER,
    periods INTEGER,            -- >4 = prodloužení
    referee1 TEXT, referee2 TEXT, referee3 TEXT,
    commissioner TEXT
);
CREATE INDEX idx_pbp_ls ON pbp(livestats_id);
CREATE INDEX idx_shots_ls ON shots(livestats_id);
"""


def gi(d, key):
    """Bezpečný int z JSONu (hodnoty bývají i string nebo chybí)."""
    v = d.get(key)
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def parse_file(path, con):
    lid = int(path.name.split(".")[0])
    d = json.loads(gzip.decompress(path.read_bytes()))

    off = d.get("officials") or {}
    con.execute(
        "INSERT OR REPLACE INTO ls_meta VALUES (?,?,?,?,?,?,?)",
        (lid, gi(d, "attendance"), gi(d, "period"),
         (off.get("referee1") or {}).get("name"),
         (off.get("referee2") or {}).get("name"),
         (off.get("referee3") or {}).get("name"),
         (off.get("commissioner") or {}).get("name")),
    )

    con.executemany(
        "INSERT INTO pbp VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (lid, gi(e, "actionNumber"), gi(e, "period"), e.get("periodType"),
             e.get("gt"), gi(e, "tno"), e.get("player") or None, e.get("shirtNumber") or None,
             e.get("actionType"), e.get("subType") or None, gi(e, "success"),
             gi(e, "s1"), gi(e, "s2"), gi(e, "lead"))
            for e in d.get("pbp", [])
        ],
    )

    for tno_s, tm in (d.get("tm") or {}).items():
        tno = int(tno_s)
        con.executemany(
            "INSERT INTO shots VALUES (?,?,?,?,?,?,?,?,?,?)",
            [
                (lid, tno, s.get("player") or None, s.get("shirtNumber") or None,
                 s.get("x"), s.get("y"), gi(s, "r"), gi(s, "per"),
                 s.get("actionType"), s.get("subType") or None)
                for s in tm.get("shot", [])
            ],
        )
        con.execute(
            "INSERT OR REPLACE INTO ls_teams VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (lid, tno, tm.get("name"), tm.get("code"),
             gi(tm, "tot_sPoints"), gi(tm, "tot_sPointsInThePaint"),
             gi(tm, "tot_sPointsFastBreak"), gi(tm, "tot_sPointsSecondChance"),
             gi(tm, "tot_sPointsFromTurnovers"), gi(tm, "tot_sBenchPoints"),
             gi(tm, "tot_sBiggestLead"), gi(tm, "tot_sBiggestScoringRun"),
             tm.get("tot_sTimeLeading")),
        )


def main():
    con = db.connect()
    con.executescript(SCHEMA)
    files = sorted((RAW / "livestats").glob("*.json.gz"))
    for i, f in enumerate(files, 1):
        try:
            parse_file(f, con)
        except Exception as e:
            print(f"  ! {f.name}: {e}")
        if i % 200 == 0:
            print(f"{i}/{len(files)}", flush=True)
            con.commit()
    con.commit()
    # doplnit návštěvnost do matches tam, kde ji máme jen z LiveStats
    con.execute(
        """UPDATE matches SET attendance = (
               SELECT m2.attendance FROM ls_meta m2 WHERE m2.livestats_id = matches.livestats_id)
           WHERE attendance IS NULL AND livestats_id IS NOT NULL""",
    )
    con.commit()
    for t in ("pbp", "shots", "ls_teams", "ls_meta"):
        print(t, con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
    con.close()


if __name__ == "__main__":
    sys.exit(main())
