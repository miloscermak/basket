# Krok 6: stáhne profily všech hráčů nalezených ve statistikách a box scores.
# Spouštět až po download_details.py (stejný server, ať netlačíme dvěma proudy).
import sys

import db
from common import BASE, RAW, fetch


def main():
    con = db.connect()
    ids = [r[0] for r in con.execute("SELECT id FROM players ORDER BY id")]
    con.close()
    print(f"Ke stažení: {len(ids)} profilů hráčů")
    done = 0
    for pid in ids:
        cache = RAW / "hrac" / f"{pid}.html.gz"
        existed = cache.exists()
        fetch(f"{BASE}/hrac/{pid}", cache)
        done += 1
        if not existed and done % 500 == 0:
            print(f"{done}/{len(ids)}", flush=True)
    print("HOTOVO")


if __name__ == "__main__":
    sys.exit(main())
