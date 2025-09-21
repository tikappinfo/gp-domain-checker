# Google Play Domain Checker

Find apps with 1M–10M installs on Google Play, normalize English titles, and check exact-match .com/.net domain availability via DNS-over-HTTPS.

## Local Run (Windows PowerShell)
```powershell
cd "c:\\Users\\Windows 10 Pro\\gp-domain-checker"
.\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
.\\.venv\\Scripts\\pip.exe install -r requirements.txt
.\\.venv\\Scripts\\python.exe -m src.main --limit 500 --out .\\data\\apps_500.csv
```
If outbound HTTPS is blocked (requests stall), use the GitHub Actions workflow below.

## Run in GitHub Actions (Bypass Local Network)
1. Initialize a git repo and push to GitHub:
```powershell
cd "c:\\Users\\Windows 10 Pro\\gp-domain-checker"
git init
git add -A
git commit -m "Add crawler and workflow"
# Create a new repo in GitHub (via UI) named gp-domain-checker, then set remote
git remote add origin https://github.com/<your-user>/gp-domain-checker.git
git branch -M main
git push -u origin main
```
2. In GitHub → Actions → "Crawl Google Play and Check Domains" → Run workflow.
3. After it finishes, download the "apps-csv" artifact; e.g., `data/apps_500.csv`.
	- The workflow also pushes the CSV to a `results` branch under `data/` so you can view/download it directly from the repo without downloading the artifact.

## Output Columns
- app_title, installs_range, normalized_label, dotcom_status, dotnet_status, notes

## Notes
- Titles are cleaned to remove " - Apps on Google Play".
- `hl=en&gl=US` enforced for consistent English titles.
- Seeds include categories, dev pages, and A–Z/0–9 searches.
- Domain availability uses Google DoH; NXDOMAIN → available.

# GP Domain Checker

Find Google Play apps with 1M–10M installs and check exact-match .com/.net availability of their normalized English titles.

## Setup (Windows PowerShell)

1. Create venv and activate:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```
pip install -r requirements.txt
```

## Run

- Generate 500-row CSV:

```
python -m src.main --limit 500 --out .\data\apps_500.csv
```

- Columns: `app_title, installs_range, normalized_label, dotcom_status, dotnet_status, notes`.

Notes:
- DNS DoH checks are a heuristic; confirm at a registrar for final availability.
- Be polite to Google Play; the scraper uses randomized UAs, retries, and delays.
