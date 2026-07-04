# Krok 3: stáhne FIBA LiveStats JSON (play-by-play, střely, návštěvnost)
# pro všechny zápasy, které ho mají.
import sys

import db
from common import LIVESTATS, RAW, fetch


def main():
    con = db.connect()
    ids = [
        r[0]
        for r in con.execute(
            "SELECT DISTINCT livestats_id FROM matches "
            "WHERE livestats_id IS NOT NULL AND home_score IS NOT NULL ORDER BY 1"
        )
    ]
    con.close()
    print(f"Ke stažení: {len(ids)} LiveStats JSONů")
    done = missing = 0
    for lid in ids:
        cache = RAW / "livestats" / f"{lid}.json.gz"
        existed = cache.exists()
        if fetch(LIVESTATS.format(lid), cache) is None:
            missing += 1
        done += 1
        if not existed and done % 200 == 0:
            print(f"{done}/{len(ids)} (404: {missing})", flush=True)
    print(f"HOTOVO (404: {missing})")


if __name__ == "__main__":
    sys.exit(main())
