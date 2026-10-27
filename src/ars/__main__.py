"""Usage: python -m ars URL [URL...] [--md] [--csv out.csv] [--delay 1.0]"""
import argparse, csv, json, sys
from .fetch import Fetcher
from .score import scan
from .report import markdown, csv_rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ars")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--md", action="store_true", help="print markdown report instead of JSON")
    ap.add_argument("--csv", help="write aggregate CSV to this path")
    ap.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args(argv)
    results = []
    for u in a.urls:
        r = scan(u, Fetcher(delay=a.delay))
        results.append(r)
        print(markdown(r) if a.md else json.dumps(r, indent=2))
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            csv.writer(f).writerows(csv_rows(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
