# SDG AI Lab – Website & Annual Report Scraper (Step-by-Step)

This toolkit downloads **key pages** (About, Mission, Strategy, Governance, etc.) and **annual/impact/sustainability reports (PDFs)** for each organization.

## 1) CSV format (Windows Desktop)
`C:\Users\Hicran Erol\OneDrive\Masaüstü\orgs_clean.csv`
```
Organization,Website
World Bank,https://www.worldbank.org/
UNIDO AIM,https://aim.unido.org/
...
```

## 2) PowerShell
```
cd "$HOME\OneDrive\Masaüstü"
python -m venv .sdgai-env
.\.sdgai-env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Run (batch)
```
mkdir scraped_output
python .\run_scrape.py `
  --csv "C:\Users\Hicran Erol\OneDrive\Masaüstü\orgs_clean.csv" `
  --out ".\scraped_output" `
  --max_pages 40 `
  --max_depth 2 `
  ````markdown
  # SDG AI Lab – Website & Annual Report Scraper (VS Code friendly)

  This toolkit downloads key pages (About, Mission, Strategy, Governance, etc.) and annual/impact/sustainability reports (PDFs) for organizations listed in a CSV.

  ## 1) CSV format
  Place your CSV in a convenient location (example path used in this repo is under your Desktop/OneDrive):
  `C:\Users\Hicran Erol\OneDrive\Masaüstü\orgs_clean.csv`

  Example CSV:
  ```
  Organization,Website
  World Bank,https://www.worldbank.org/
  UNIDO AIM,https://aim.unido.org/
  ...
  ```

  ## 2) Recommended: use Visual Studio Code
  - Open the project folder in VS Code.
  - Use the integrated terminal and choose a shell you prefer (Command Prompt, Git Bash, or WSL). This avoids PowerShell execution-policy issues.

  ### Create & activate a virtual environment
  Command Prompt (cmd.exe):
  ```bat
  cd "%USERPROFILE%\\OneDrive\\Masaüstü\\sdgai_toolkit_vscode"
  python -m venv .sdgai-env
  .sdgai-env\Scripts\activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

  Git Bash / WSL:
  ```bash
  cd "$HOME/OneDrive/Masaüstü/sdgai_toolkit_vscode"
  python -m venv .sdgai-env
  source .sdgai-env/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

  ## 3) Quick smoke-test (fast verification)
  Run a small crawl to confirm everything works:
  ```bash
  python run_scrape.py --org "Example Org" --url "https://example.com" --out "./scraped_output" --max_pages 5 --max_depth 1 --delay 1.0
  ```

  ## 4) Run the full batch (CSV)
  Create the output folder and run with your CSV:
  ```bash
  mkdir scraped_output
  python run_scrape.py --csv "C:\Users\Hicran Erol\OneDrive\Masaüstü\orgs_clean.csv" --out "./scraped_output" --max_pages 40 --max_depth 2 --delay 1.5
  ```

  ## 5) VS Code Run/Debug helpers
  - Add a `launch.json` configuration (Run & Debug → create) to run `run_scrape.py` with args. Example:
  ```json
  {
    "name": "Run scrape (example)",
    "type": "python",
    "request": "launch",
    "module": "run_scrape",
    "args": ["--org","Example Org","--url","https://example.com","--out","${workspaceFolder}/scraped_output","--max_pages","5","--max_depth","1","--delay","1.0"]
  }
  ```

  - Optional `tasks.json` to automate venv creation + install (Command Prompt):
  ```json
  {
    "label": "setup-venv",
    "type": "shell",
    "command": "python -m venv .sdgai-env && .\.sdgai-env\\Scripts\\activate && python -m pip install --upgrade pip && pip install -r requirements.txt",
    "problemMatcher": []
  }
  ```

  ## 6) Where outputs and logs appear
  - For each organization the tool creates: `scraped_output/<slug>/html/`, `scraped_output/<slug>/pdfs/`, and `scraped_output/<slug>/meta.jsonl`.
  - Inspect `meta.jsonl` for events like `save_page`, `save_pdf`, `error`, `disallowed`, `pdf_too_large`.

  ## Notes & troubleshooting
  - `run_scrape.py` matches CSV headers case-insensitively for common variants (`Organization`, `Website`, `Org`, `URL`).
  - If you run into activation policy issues only in PowerShell, prefer Command Prompt or Git Bash inside VS Code.
  - If network errors occur, check `meta.jsonl` and look for `error` events with HTTP status codes.

  ````
