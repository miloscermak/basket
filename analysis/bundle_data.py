# Zabalí JSONy z web/data/ do web/data.js, aby web fungoval i při otevření
# souboru napřímo (file:// nedovolí fetch). Spouštět po každém build_*.py.
import json
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"


def main():
    bundle = {}
    for f in sorted((WEB / "data").glob("*.json")):
        bundle[f.stem] = json.loads(f.read_text())
    (WEB / "data.js").write_text(
        "// Vygenerováno skriptem analysis/bundle_data.py — needitovat ručně.\n"
        "window.BASKET_DATA = " + json.dumps(bundle, ensure_ascii=False) + ";\n"
    )
    print("OK -> web/data.js:", ", ".join(bundle))


if __name__ == "__main__":
    sys.exit(main())
