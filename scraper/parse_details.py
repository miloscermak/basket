# Krok 4: z cachovaných detailů zápasů vytěží box scores (individuální
# statistiky hráčů) a návštěvnost. Hlavičky tabulek se mezi úrovněmi liší
# (NBL má plný FIBA box, krajský přebor jen body), parsuje se podle hlavičky.
import gzip
import re
import sys

from bs4 import BeautifulSoup

import db
from common import RAW

# normalizovaná hlavička -> sloupec v DB (dvojice made/attempt řeší split())
COL_MAP = {
    "min.": "minutes",
    "2b": ("p2m", "p2a"),
    "3b": ("p3m", "p3a"),
    "th": ("ftm", "fta"),
    "du": "oreb",
    "dú": "oreb",
    "do": "dreb",
    "dc": "reb",
    "bl": "blk",
    "as": "ast",
    "m+": "stl",
    "m-": "tov",
    "f+": "fouls_drawn",
    "f-": "fouls",
    "f": "fouls",
    "val": "val",
    "b": "pts",
    "+/-": "plus_minus",
}

STAT_COLS = [
    "minutes", "p2m", "p2a", "p3m", "p3a", "ftm", "fta", "oreb", "dreb", "reb",
    "blk", "ast", "stl", "tov", "fouls_drawn", "fouls", "val", "pts", "plus_minus",
]


def parse_boxscore_tables(soup):
    """Najde tabulky box score (hlavička 'Číslo, Hráč, ...') v pořadí domácí, hosté."""
    out = []
    for table in soup.find_all("table"):
        header = table.find("tr")
        if not header:
            continue
        cols = [c.get_text(" ", strip=True).lower() for c in header.find_all(["th", "td"])]
        if len(cols) >= 2 and cols[0].startswith("číslo") and cols[1].startswith("hráč"):
            out.append((table, cols))
    return out[:2]


def parse_player_row(tr, cols):
    tds = tr.find_all("td")
    link = tr.find("a", href=re.compile(r"/hrac/\d+"))
    if not link or len(tds) < 2:
        return None
    rec = {c: None for c in STAT_COLS}
    rec["player_id"] = int(re.search(r"/hrac/(\d+)", link["href"]).group(1))
    rec["name"] = link.get_text(" ", strip=True)
    rec["jersey"] = tds[0].get_text(strip=True) or None
    for i, col in enumerate(cols):
        if i >= len(tds):
            break
        target = COL_MAP.get(col)
        if not target:
            continue
        text = tds[i].get_text(" ", strip=True)
        if isinstance(target, tuple):
            nums = re.findall(r"-?\d+", text)
            if len(nums) >= 2:
                rec[target[0]], rec[target[1]] = int(nums[0]), int(nums[1])
            elif len(nums) == 1:
                rec[target[0]], rec[target[1]] = int(nums[0]), int(nums[0]) if nums[0] == "0" else None
        elif target == "minutes":
            rec["minutes"] = text or None
        else:
            m = re.search(r"-?\d+", text)
            rec[target] = int(m.group(0)) if m else None
    return rec


def parse_match(html, match_id, con):
    soup = BeautifulSoup(html, "lxml")

    attendance = None
    m = re.search(r"Diváci:</span>\s*(\d+)", html)
    if m:
        attendance = int(m.group(1))

    # ID týmů z hlavičky zápasu (první dva odkazy /tym/ v h1)
    home_tid = away_tid = None
    h1 = soup.find("h1")
    if h1:
        tids = [int(x) for x in re.findall(r"/tym/(\d+)", str(h1))]
        if len(tids) >= 2:
            home_tid, away_tid = tids[0], tids[1]

    con.execute(
        "UPDATE matches SET attendance=?, home_team_id=?, away_team_id=?, detail_parsed=1 WHERE id=?",
        (attendance, home_tid, away_tid, match_id),
    )

    for side, (table, cols) in enumerate(parse_boxscore_tables(soup), start=1):
        for tr in table.find_all("tr")[1:]:
            rec = parse_player_row(tr, cols)
            if not rec:
                continue
            con.execute(
                "INSERT OR IGNORE INTO players (id, name) VALUES (?,?)",
                (rec["player_id"], rec["name"]),
            )
            con.execute(
                f"""INSERT OR REPLACE INTO boxscores
                    (match_id, team_side, player_id, jersey, name, {','.join(STAT_COLS)})
                    VALUES (?,?,?,?,?,{','.join('?' * len(STAT_COLS))})""",
                (match_id, side, rec["player_id"], rec["jersey"], rec["name"],
                 *[rec[c] for c in STAT_COLS]),
            )


def main():
    con = db.connect()
    ids = [
        r[0]
        for r in con.execute(
            "SELECT id FROM matches WHERE home_score IS NOT NULL AND detail_parsed=0 ORDER BY id"
        )
    ]
    print(f"K parsování: {len(ids)} zápasů")
    done = skipped = 0
    for mid in ids:
        cache = RAW / "zapas" / f"{mid}.html.gz"
        if not cache.exists():
            skipped += 1
            continue
        html = gzip.decompress(cache.read_bytes()).decode("utf-8", errors="replace")
        parse_match(html, mid, con)
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(ids)}", flush=True)
            con.commit()
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM boxscores").fetchone()[0]
    np = con.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    print(f"HOTOVO: parsováno {done}, bez cache {skipped}; boxscore řádků {n}, hráčů {np}")
    con.close()


if __name__ == "__main__":
    sys.exit(main())
