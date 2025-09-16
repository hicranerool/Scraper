# run_scrape.py
import argparse, os, pandas as pd
from scraper import crawl

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="CSV with columns: Organization,Website")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--max_pages", type=int, default=40)
    ap.add_argument("--max_depth", type=int, default=2)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--patterns", default="patterns.json")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    df = pd.read_csv(args.csv)

    possible_org_cols = [c for c in df.columns if c.strip().lower() in ("organization", "organisation", "org", "name")]
    possible_web_cols = [c for c in df.columns if c.strip().lower() in ("website", "url", "root", "homepage")]

    if not possible_org_cols or not possible_web_cols:
        raise SystemExit("CSV must have headers 'Organization' and 'Website' (case-insensitive).")

    org_col = possible_org_cols[0]
    web_col = possible_web_cols[0]

    for _, row in df.iterrows():
        org = str(row[org_col]).strip()
        url = str(row[web_col]).strip()
        if not org or not url or url.lower() == "nan":
            continue
        print(f"==> {org} :: {url}")
        crawl(org, url, args.out, args.max_pages, args.max_depth, args.delay, args.patterns)

if __name__ == "__main__":
    main()