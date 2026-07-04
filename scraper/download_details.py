# Krok 2: stáhne detailní stránky všech odehraných zápasů (kvůli box scores
# a ID hráčů). Stránky se cachují na disk, opakované spuštění naváže tam,
# kde skončilo.
import sys

import db
from common import BASE, RAW, fetch


def main():
    con = db.connect()
    ids = [
        r[0]
        for r in con.execute(
            "SELECT id FROM matches WHERE home_score IS NOT NULL ORDER BY id"
        )
    ]
    con.close()
    print(f"Ke stažení: {len(ids)} zápasů")
    done = 0
    for mid in ids:
        cache = RAW / "zapas" / f"{mid}.html.gz"
        existed = cache.exists()
        fetch(f"{BASE}/zapas/{mid}", cache)
        done += 1
        if not existed and done % 200 == 0:
            print(f"{done}/{len(ids)}", flush=True)
    print("HOTOVO")


if __name__ == "__main__":
    sys.exit(main())
