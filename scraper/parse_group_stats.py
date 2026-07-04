# Krok 5: z cachovaných stránek skupin vytěží sezónní statistiky hráčů
# (průměry na zápas, věk, pozici, tým). Ty jsou k dispozici i tam,
# kde se nevedou zápisy po zápasech.
import gzip
import re
import sys

import db
from bs4 import BeautifulSoup
from common import RAW

SCHEMA = """
CREATE TABLE IF NOT EXISTS player_group_stats (
    player_id INTEGER,
    group_id INTEGER,
    name TEXT,
    team TEXT,
    position TEXT,
    age INTEGER,
    games INTEGER,
    min_avg REAL, pts_avg REAL,
    p2m_avg REAL, p2a_avg REAL, p2_pct REAL,
    p3m_avg REAL, p3a_avg REAL, p3_pct REAL,
    ftm_avg REAL, fta_avg REAL, ft_pct REAL,
    oreb_avg REAL, dreb_avg REAL, reb_avg REAL,
    ast_avg REAL, stl_avg REAL, tov_avg REAL,
    fd_avg REAL, fc_avg REAL,
    val_avg REAL, pm_avg REAL,
    PRIMARY KEY (player_id, group_id)
);
"""

PAIRS = {"2b": ("p2m_avg", "p2a_avg"), "3b": ("p3m_avg", "p3a_avg"), "th": ("ftm_avg", "fta_avg")}
SINGLES = {
    "věk": "age", "z": "games", "min.": "min_avg", "b": "pts_avg",
    "2b %": "p2_pct", "3b %": "p3_pct", "th %": "ft_pct",
    "dú": "oreb_avg", "do": "dreb_avg", "dc": "reb_avg",
    "as": "ast_avg", "m+": "stl_avg", "m-": "tov_avg",
    "f+": "fd_avg", "f-": "fc_avg", "val": "val_avg", "+/-": "pm_avg",
}


def find_stats_table(soup):
    """Statistická tabulka hráčů: obsahuje sloupce Hráč, Tým i Z (počet zápasů)."""
    for table in soup.find_all("table"):
        header = table.find("tr")
        if not header:
            continue
        cols = [c.get_text(" ", strip=True).lower() for c in header.find_all(["th", "td"])]
        if "hráč" in cols and "tým" in cols and "z" in cols:
            return table, cols
    return None, None


def num(text):
    m = re.search(r"-?\d+(?:\.\d+)?", text.replace(",", "."))
    return float(m.group(0)) if m else None


def parse_group(html, gid, con):
    soup = BeautifulSoup(html, "lxml")
    table, cols = find_stats_table(soup)
    if not table:
        return 0
    n = 0
    for tr in table.find_all("tr")[1:]:
        link = tr.find("a", href=re.compile(r"/hrac/\d+"))
        tds = tr.find_all("td")
        if not link or len(tds) < 5:
            continue
        rec = {v: None for v in list(SINGLES.values()) + [x for p in PAIRS.values() for x in p]}
        rec["player_id"] = int(re.search(r"/hrac/(\d+)", link["href"]).group(1))
        rec["name"] = link.get_text(" ", strip=True)
        rec["team"] = rec["position"] = None
        for i, col in enumerate(cols):
            if i >= len(tds):
                break
            text = tds[i].get_text(" ", strip=True)
            if col == "tým":
                rec["team"] = text or None
            elif col == "pozice":
                rec["position"] = text or None
            elif col in PAIRS:
                nums = re.findall(r"-?\d+(?:\.\d+)?", text)
                if len(nums) >= 2:
                    rec[PAIRS[col][0]], rec[PAIRS[col][1]] = float(nums[0]), float(nums[1])
            elif col in SINGLES:
                v = num(text)
                if col == "věk":
                    # občas je v buňce rok narození apod. – nesmysly zahazujeme
                    rec["age"] = int(v) if v is not None and 5 <= v <= 80 else None
                elif col == "z":
                    rec[SINGLES[col]] = int(v) if v is not None else None
                else:
                    rec[SINGLES[col]] = v
        keys = ["player_id", "name", "team", "position"] + list(
            dict.fromkeys(list(SINGLES.values()) + [x for p in PAIRS.values() for x in p])
        )
        con.execute(
            f"INSERT OR REPLACE INTO player_group_stats (group_id, {','.join(keys)}) "
            f"VALUES (?, {','.join('?' * len(keys))})",
            (gid, *[rec[k] for k in keys]),
        )
        con.execute("INSERT OR IGNORE INTO players (id, name) VALUES (?,?)",
                    (rec["player_id"], rec["name"]))
        n += 1
    return n


def main():
    con = db.connect()
    con.executescript(SCHEMA)
    groups = con.execute(
        "SELECT g.id, g.competition_id FROM groups g ORDER BY g.id"
    ).fetchall()
    total = 0
    for i, (gid, sid) in enumerate(groups, 1):
        cache = RAW / "soutez" / f"{sid}_{gid}.html.gz"
        if not cache.exists():
            continue
        html = gzip.decompress(cache.read_bytes()).decode("utf-8", errors="replace")
        total += parse_group(html, gid, con)
        if i % 100 == 0:
            print(f"{i}/{len(groups)} skupin, {total} řádků", flush=True)
            con.commit()
    con.commit()
    np = con.execute("SELECT COUNT(DISTINCT player_id) FROM player_group_stats").fetchone()[0]
    print(f"HOTOVO: {total} statistických řádků, {np} unikátních hráčů")
    con.close()


if __name__ == "__main__":
    sys.exit(main())
