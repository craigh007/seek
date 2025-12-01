# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Selenium-based web scraper for Seek.co.nz job listings with SQLite database storage and a Flask web viewer. Designed for incremental scraping (2-3 times daily) to build a comprehensive jobs database.

## Commands

### Run the scraper
```powershell
python seek_scraper_selenium.py
```
Scrapes last 3 days of listings, deduplicates, and stores in `jobs.db`.

### Query the database
```powershell
python query_jobs.py --stats              # Database statistics
python query_jobs.py --today              # Jobs added today
python query_jobs.py --days 7             # Jobs from last 7 days
python query_jobs.py --search "keyword"   # Search by keyword
python query_jobs.py --location "Auckland"
python query_jobs.py --all --export-csv output.csv
```

### Web viewer
```powershell
python web_viewer.py
```
Starts Flask server at http://localhost:5500 with triage functionality.

### Import historical CSV
```powershell
python import_csv.py <csv_file>
```

## Architecture

### Core Components

- **`seek_scraper_selenium.py`**: Main scraper with two classes:
  - `JobDatabase`: SQLite manager with advanced duplicate detection (checks URL, then title+company+location+description)
  - `SeekSeleniumScraper`: Selenium-based scraper with anti-detection measures, relative date parsing (converts "2 hours ago" to NZ date format)

- **`query_jobs.py`**: CLI query tool wrapping `JobsQuery` class for database searches and exports

- **`web_viewer.py`**: Flask API with triage status tracking (yes/gsv/no), serves `jobs_viewer.html`

### Database Schema (`jobs.db`)

```sql
jobs (
    id, url UNIQUE, title, company, location, salary,
    date_listed, job_type, description,
    first_seen, last_seen, is_active, triage_status
)
```
Indexed on: url, date_listed, first_seen

### Key Behaviors

- Duplicate detection: First by URL, then by title+company+location+description(first 200 chars)
- Date parsing: Converts relative dates ("6 hours ago") to NZ timezone DD/MM/YYYY format
- Scraper config: Modify lines 1023-1029 for `daterange` (1/3/7/14/31 days) and `max_pages`
- Headless mode: Set `headless=True` on line 1012

## Dependencies

Install with: `pip install -r requirements_selenium.txt`
- selenium, beautifulsoup4, lxml, requests, pytz
- Flask, flask-cors (for web viewer)
- Requires Chrome browser and ChromeDriver in PATH
