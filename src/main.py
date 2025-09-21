import argparse, csv, os, re
from typing import Dict
import pandas as pd

from .google_play import crawl, SEED_URLS
from .dns_check import check_pair

def normalize_label(title: str) -> str:
    label = re.sub(r"[^a-z0-9]", "", title.lower())
    return label[:63] if label else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500, help="Number of apps to collect (1M–10M installs)")
    ap.add_argument("--out", type=str, default="./data/apps_500.csv", help="Output CSV path")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    print(f"Crawling Google Play seeds (target rows={args.limit})...")
    apps = crawl(SEED_URLS, max_items=args.limit * 2)
    print(f"Found {len(apps)} apps in range (1M–10M)")
    rows = []
    seen_labels = set()

    for app in apps:
        if len(rows) >= args.limit:
            break
        title = app["title"]
        installs = app["installs"]
        label = normalize_label(title)
        if not label or label in seen_labels:
            continue
        seen_labels.add(label)
        domain_status = check_pair(label)
        row: Dict = {
            "app_title": title,
            "installs_range": installs,
            "normalized_label": label,
            "dotcom_status": domain_status["dotcom_status"],
            "dotnet_status": domain_status["dotnet_status"],
            "notes": "",
        }
        rows.append(row)
        if len(rows) % 25 == 0:
            print(f"Progress: {len(rows)} rows prepared...")

    import pandas as pd
    df = pd.DataFrame(rows, columns=["app_title", "installs_range", "normalized_label", "dotcom_status", "dotnet_status", "notes"])
    df.to_csv(args.out, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Wrote {len(df)} rows to {args.out}")

if __name__ == "__main__":
    main()
