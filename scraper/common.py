# Společné nástroje pro stahování: session, rate limit, cache na disku.
import gzip
import time
from pathlib import Path

import requests

BASE = "https://cz.basketball"
LIVESTATS = "https://fibalivestats.dcd.shared.geniussports.com/data/{}/data.json"

DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw"
DB_PATH = DATA / "basket.sqlite"

# Slušné tempo: pauza mezi requesty, ať portál nezatěžujeme.
DELAY = 0.4

_session = requests.Session()
_session.headers["User-Agent"] = (
    "basket-research/0.1 (datova analyza sezony; kontakt: extracermak@gmail.com)"
)
_last_request = 0.0


def fetch(url: str, cache_file: Path, *, force: bool = False) -> bytes | None:
    """Stáhne URL s rate limitem a uloží gzipnutou cache. Vrací obsah, None při 404."""
    global _last_request
    if cache_file.exists() and not force:
        return gzip.decompress(cache_file.read_bytes())

    for attempt in range(4):
        wait = DELAY - (time.time() - _last_request)
        if wait > 0:
            time.sleep(wait)
        try:
            _last_request = time.time()
            resp = _session.get(url, timeout=30)
        except requests.RequestException as e:
            print(f"  ! {url}: {e}, pokus {attempt + 1}")
            time.sleep(2**attempt)
            continue
        if resp.status_code == 404:
            return None
        if resp.status_code != 200:
            print(f"  ! {url}: HTTP {resp.status_code}, pokus {attempt + 1}")
            time.sleep(2**attempt)
            continue
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(gzip.compress(resp.content))
        return resp.content
    raise RuntimeError(f"Nepodařilo se stáhnout {url}")
