# Krok 1: projde všechny soutěže sezóny 2025/26 (celostátní + oblasti)
# a uloží do databáze soutěže, skupiny a všechny zápasy včetně haly,
# rozhodčích a komisaře (to vše je přímo v rozpisové tabulce skupiny).
import json
import re
import sys

from bs4 import BeautifulSoup

import db
from common import BASE, RAW, fetch

SEASON = "2025/26"
YEAR = 2025
AREAS = list(range(15))  # 0 = celá ČR, ostatní oblasti; neexistující vrátí prázdno

DATE_RE = re.compile(r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})")


def find_schedule_table(soup):
    """Rozpisová tabulka má v hlavičce sloupec 'domácí / hosté'."""
    for table in soup.find_all("table"):
        header = table.find("tr")
        if header and "domácí" in header.get_text(" ", strip=True).lower():
            cols = [th.get_text(" ", strip=True).lower() for th in header.find_all(["th", "td"])]
            return table, cols
    return None, None


def cell(tds, cols, name):
    """Vrátí buňku podle názvu sloupce v hlavičce, jinak None."""
    for i, c in enumerate(cols):
        if name in c and i < len(tds):
            return tds[i]
    return None


def parse_match_row(tr, cols):
    """Z řádku rozpisové tabulky vytáhne data zápasu."""
    link = tr.find("a", href=re.compile(r"^/zapas/\d+"))
    if not link:
        return None
    match_id = int(re.search(r"/zapas/(\d+)", link["href"]).group(1))
    tds = tr.find_all("td")

    def txt(name):
        c = cell(tds, cols, name)
        return c.get_text(" ", strip=True) if c else None

    date_iso = time_txt = None
    dt = txt("datum")
    if dt:
        m = DATE_RE.search(dt)
        if m:
            date_iso = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
        t = re.search(r"(\d{1,2}:\d{2})", dt)
        time_txt = t.group(1) if t else None

    home = away = None
    c = cell(tds, cols, "domácí")
    if c:
        teams = [d.get_text(strip=True) for d in c.find_all("div")]
        if len(teams) >= 2:
            home, away = teams[0], teams[1]

    home_score = away_score = None
    c = cell(tds, cols, "skore")
    if c:
        nums = re.findall(r"\d+", c.get_text(" ", strip=True))
        if len(nums) >= 2:
            home_score, away_score = int(nums[0]), int(nums[1])

    quarters, livestats_id = None, None
    c = cell(tds, cols, "čtvrtiny")
    if c:
        qs = []
        for d in c.find_all("div"):
            q = re.findall(r"\d+", d.get_text(" ", strip=True))
            if len(q) == 2:
                qs.append([int(q[0]), int(q[1])])
        quarters = json.dumps(qs) if qs else None
        ls = c.find("a", href=re.compile(r"fibalivestats"))
        if ls:
            lm = re.search(r"/(\d+)/?$", ls["href"])
            livestats_id = int(lm.group(1)) if lm else None

    c = cell(tds, cols, "rozhodčí")
    referees = "; ".join(s.strip() for s in c.stripped_strings) if c else None

    return {
        "id": match_id,
        "round": txt("kolo"),
        "game_number": txt("číslo"),
        "date": date_iso,
        "time": time_txt,
        "home": home,
        "away": away,
        "home_score": home_score,
        "away_score": away_score,
        "quarters": quarters,
        "livestats_id": livestats_id,
        "venue": txt("místo"),
        "referees": referees,
        "commissioner": txt("komisař"),
    }


def main():
    con = db.connect()
    # 1) posbírat (soutez_id, group_id, text, area) ze všech oblastních indexů
    pairs = {}
    for area in AREAS:
        html = fetch(f"{BASE}/soutez?y={YEAR}&area={area}", RAW / "index" / f"area_{area}.html.gz")
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        n = 0
        for a in soup.find_all("a", href=re.compile(r"^/soutez/\d+\?p=\d+")):
            sid, gid = map(int, re.search(r"/soutez/(\d+)\?p=(\d+)", a["href"]).groups())
            txt = a.get_text(" ", strip=True)
            if gid not in pairs:
                pairs[gid] = (sid, txt, area)
                n += 1
        print(f"area {area}: +{n} skupin", flush=True)
    print(f"celkem skupin: {len(pairs)}", flush=True)

    # 2) stáhnout stránku každé skupiny a vytěžit zápasy
    total = 0
    for i, (gid, (sid, gname, area)) in enumerate(sorted(pairs.items()), 1):
        html = fetch(f"{BASE}/soutez/{sid}?p={gid}", RAW / "soutez" / f"{sid}_{gid}.html.gz")
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        h1 = soup.find("h1")
        comp_name = h1.get_text(" ", strip=True) if h1 else None
        con.execute(
            "INSERT OR REPLACE INTO competitions (id, name, area, season) VALUES (?,?,?,?)",
            (sid, comp_name, area, SEASON),
        )
        con.execute(
            "INSERT OR REPLACE INTO groups (id, competition_id, name) VALUES (?,?,?)",
            (gid, sid, gname),
        )
        table, cols = find_schedule_table(soup)
        rows = 0
        if table:
            for tr in table.find_all("tr")[1:]:
                rec = parse_match_row(tr, cols)
                if not rec:
                    continue
                con.execute(
                    """INSERT INTO matches (id, group_id, round, game_number, date, time,
                           home, away, home_score, away_score, quarters, livestats_id,
                           venue, referees, commissioner)
                       VALUES (:id, :group_id, :round, :game_number, :date, :time,
                           :home, :away, :home_score, :away_score, :quarters, :livestats_id,
                           :venue, :referees, :commissioner)
                       ON CONFLICT(id) DO UPDATE SET
                           group_id=:group_id, round=:round, quarters=:quarters,
                           home_score=:home_score, away_score=:away_score,
                           venue=:venue, referees=:referees, commissioner=:commissioner,
                           livestats_id=COALESCE(:livestats_id, livestats_id)""",
                    {**rec, "group_id": gid},
                )
                rows += 1
        total += rows
        if i % 25 == 0:
            print(f"[{i}/{len(pairs)}] {comp_name} / {gname}: {rows} zápasů (celkem {total})", flush=True)
        con.commit()

    n_matches = con.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
    n_ls = con.execute("SELECT COUNT(*) FROM matches WHERE livestats_id IS NOT NULL").fetchone()[0]
    print(f"\nHOTOVO: {n_matches} zápasů, z toho {n_ls} s LiveStats")
    con.close()


if __name__ == "__main__":
    sys.exit(main())
