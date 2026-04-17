# competitor-price-scraper

Scrapes competitor pricing data from https://books.toscrape.com using Playwright, stores results in SQLite, exports a daily CSV report, and emails the report to a configured recipient.

## Features

- Scrapes book title, price, and rating
- Stores history in SQLite (`prices.db`)
- Exports daily CSV reports
- Emails report via SMTP
- Scheduler with `schedule`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
cp .env.example .env
# update SMTP + export settings
```

## Run

```bash
python scraper.py
```

## Environment Variables

- `DB_PATH` (default `prices.db`)
- `EXPORT_DIR` (default `exports`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`
- `MAIL_TO`
