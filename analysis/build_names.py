# Vygeneruje web/data/names.json — nejčastější příjmení, rodinné klany
# a soutěže s největším věkovým rozpětím.
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"


def surname(name):
    """Poslední slovo jména; ženská -ová se normalizuje na mužský tvar."""
    parts = name.strip().split()
    if not parts:
        return None
    s = parts[-1]
    if len(s) < 3:
        return None
    return s


def make_normalizer(raw_counts):
    """Vrátí funkci ženský tvar -> mužský. Ženská příjmení mají víc mužských
    kandidátů (Nováková->Novák, Svobodová->Svoboda, Novotná->Novotný);
    vybíráme tvar, který v datech skutečně existuje."""
    def norm(s):
        if s.endswith("ová"):
            c1, c2 = s[:-3], s[:-3] + "a"
            return c2 if raw_counts.get(c2, 0) > raw_counts.get(c1, 0) else c1
        if s.endswith("á"):
            c = s[:-1] + "ý"
            return c if raw_counts.get(c) else s
        return s
    return norm


def main():
    con = sqlite3.connect(ROOT / "data" / "basket.sqlite", timeout=60)
    con.row_factory = sqlite3.Row
    d = {}

    # nejčastější příjmení (muži + ženy dohromady přes normalizaci)
    raw = Counter()
    all_names = [row[0] for row in con.execute("SELECT name FROM players")]
    for name in all_names:
        s = surname(name or "")
        if s:
            raw[s] += 1
    normalized = make_normalizer(raw)

    counts = Counter()
    variants = defaultdict(Counter)
    for name in all_names:
        s = surname(name or "")
        if not s:
            continue
        n = normalized(s)
        counts[n] += 1
        variants[n][s] += 1
    d["prijmeni"] = [
        {"prijmeni": n, "hracu": c,
         "tvary": ", ".join(f"{v} ({k})" for v, k in variants[n].most_common(2))}
        for n, c in counts.most_common(15)
    ]
    d["prijmeni_celkem"] = len(counts)

    # rodinné klany: 3+ hráčů stejného (normalizovaného) příjmení ve stejném týmu
    clans = defaultdict(set)
    for row in con.execute("SELECT DISTINCT player_id, name, team FROM player_group_stats"):
        s = surname(row["name"] or "")
        if s and row["team"]:
            clans[(row["team"], normalized(s))].add(row["name"])
    # velmi častá příjmení nejsou "rodina" — náhodné shody Nováků v jednom klubu
    clans = {k: v for k, v in clans.items() if counts[k[1]] < 40}
    d["klany"] = [
        {"tym": team, "prijmeni": surn, "hracu": len(names),
         "jmena": ", ".join(sorted(names))}
        for (team, surn), names in sorted(clans.items(), key=lambda kv: -len(kv[1]))
        if len(names) >= 3
    ][:12]

    # věkové rozpětí dospělých soutěží (hráči s 3+ zápasy)
    d["vekova_rozpeti"] = [
        dict(row)
        for row in con.execute("""
            SELECT c.name soutez, c.area,
                   MIN(s.age) nejmladsi, MAX(s.age) nejstarsi,
                   MAX(s.age)-MIN(s.age) rozpeti,
                   (SELECT s2.name FROM player_comp_stats s2
                    WHERE s2.competition_id=s.competition_id AND s2.games>=3
                    ORDER BY s2.age LIMIT 1) jmeno_nejmladsi,
                   (SELECT s3.name FROM player_comp_stats s3
                    WHERE s3.competition_id=s.competition_id AND s3.games>=3
                    ORDER BY s3.age DESC LIMIT 1) jmeno_nejstarsi
            FROM player_comp_stats s
            JOIN competitions c ON c.id=s.competition_id
            WHERE LOWER(c.category) IN ('muži','ženy') AND s.games>=3 AND s.age IS NOT NULL
            GROUP BY s.competition_id
            ORDER BY rozpeti DESC LIMIT 10""")
    ]

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "names.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print("OK -> names.json")
    print("top příjmení:", d["prijmeni"][0] if d["prijmeni"] else None)
    print("top klan:", d["klany"][0] if d["klany"] else None)
    print("top rozpětí:", d["vekova_rozpeti"][0] if d["vekova_rozpeti"] else None)


if __name__ == "__main__":
    sys.exit(main())
