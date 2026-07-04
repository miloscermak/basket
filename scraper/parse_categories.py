# Krok 9: z cachovaných indexů soutěží vytěží kategorii (Muži, Ženy, U19…U11)
# — indexová stránka má taby a v každém tab-pane jsou odkazy na soutěže.
import gzip
import re
import sys

import db
from bs4 import BeautifulSoup
from common import RAW


def main():
    con = db.connect()
    con.execute("ALTER TABLE competitions ADD COLUMN category TEXT")
    mapping = {}
    for f in sorted((RAW / "index").glob("area_*.html.gz")):
        html = gzip.decompress(f.read_bytes()).decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "lxml")
        for tab in soup.find_all("a", href=re.compile(r"^#tab-pane-\d+")):
            label = tab.get_text(" ", strip=True)
            pane = soup.find(id=tab["href"][1:])
            if not pane or not label:
                continue
            for a in pane.find_all("a", href=re.compile(r"^/soutez/\d+")):
                sid = int(re.search(r"/soutez/(\d+)", a["href"]).group(1))
                mapping.setdefault(sid, label)
    for sid, label in mapping.items():
        con.execute("UPDATE competitions SET category=? WHERE id=?", (label, sid))
    con.commit()
    print(f"kategorií přiřazeno: {len(mapping)}")
    for row in con.execute(
        "SELECT category, COUNT(*) FROM competitions GROUP BY 1 ORDER BY 2 DESC"
    ):
        print(row)
    con.close()


if __name__ == "__main__":
    sys.exit(main())
