# Krok 7: z cachovaných profilů hráčů vytěží kariéru po sezónách
# a osobní rekordy.
import gzip
import re
import sys

import db
from bs4 import BeautifulSoup
from common import RAW

SCHEMA = """
DROP TABLE IF EXISTS player_seasons;
CREATE TABLE player_seasons (
    player_id INTEGER,
    season TEXT,                 -- '2007/08'
    phase TEXT,                  -- 'muži - základní část' apod.
    team TEXT,
    games INTEGER,
    min_avg REAL,
    pts_avg REAL,
    PRIMARY KEY (player_id, season, phase, team)
);
CREATE TABLE IF NOT EXISTS player_records (
    player_id INTEGER,
    stat TEXT,
    value REAL,
    opponent TEXT,
    date TEXT,
    season TEXT,
    PRIMARY KEY (player_id, stat)
);
"""

DATE_RE = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")


def num(text):
    m = re.search(r"-?\d+(?:[.,]\d+)?", text)
    return float(m.group(0).replace(",", ".")) if m else None


def parse_player(html, pid, con):
    soup = BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        header = table.find("tr")
        if not header:
            continue
        cols = [c.get_text(" ", strip=True).lower() for c in header.find_all(["th", "td"])]
        if cols[:2] == ["sezona", "tým"]:
            for tr in table.find_all("tr")[1:]:
                tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(tds) < 4:
                    continue
                m = re.match(r"(\d{4}/\d{2})\s*(.*)", tds[0])
                if not m:
                    continue
                games = num(tds[2])
                con.execute(
                    "INSERT OR REPLACE INTO player_seasons VALUES (?,?,?,?,?,?,?)",
                    (pid, m.group(1), m.group(2).strip(" -") or None, tds[1] or None,
                     int(games) if games else None, num(tds[3]), num(tds[4])),
                )
        elif cols[:2] == ["rekord", "hodnota rekordu"] and len(cols) >= 5:
            for tr in table.find_all("tr")[1:]:
                tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(tds) < 5 or not tds[0]:
                    continue
                dm = DATE_RE.search(tds[3])
                date_iso = (
                    f"{dm.group(3)}-{int(dm.group(2)):02d}-{int(dm.group(1)):02d}" if dm else None
                )
                con.execute(
                    "INSERT OR REPLACE INTO player_records VALUES (?,?,?,?,?,?)",
                    (pid, tds[0], num(tds[1]), tds[2] or None, date_iso, tds[4] or None),
                )


def main():
    con = db.connect()
    con.executescript(SCHEMA)
    ids = [r[0] for r in con.execute("SELECT id FROM players ORDER BY id")]
    done = skipped = 0
    for pid in ids:
        cache = RAW / "hrac" / f"{pid}.html.gz"
        if not cache.exists():
            skipped += 1
            continue
        html = gzip.decompress(cache.read_bytes()).decode("utf-8", errors="replace")
        parse_player(html, pid, con)
        done += 1
        if done % 1000 == 0:
            print(f"{done}/{len(ids)}", flush=True)
            con.commit()
    con.commit()
    ns = con.execute("SELECT COUNT(*) FROM player_seasons").fetchone()[0]
    nr = con.execute("SELECT COUNT(*) FROM player_records").fetchone()[0]
    print(f"HOTOVO: parsováno {done} profilů (bez cache {skipped}); {ns} sezónních řádků, {nr} rekordů")
    con.close()


if __name__ == "__main__":
    sys.exit(main())
