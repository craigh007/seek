# Seek Job Scraper - SQLite Database Version

## Overview

This scraper now uses SQLite to automatically track and deduplicate job listings. Run it 2-3 times daily to build a comprehensive jobs database.

## Files

- `seek_scraper_selenium.py` - Main scraper with SQLite integration
- `query_jobs.py` - Helper script to query and export data
- `jobs.db` - SQLite database (created automatically)

## Quick Start

### Run the scraper

```powershell
python seek_scraper_selenium.py
```

The scraper will:
- Scrape last 3 days of job listings from Seek.co.nz
- Automatically skip duplicates (based on job URL)
- Update `last_seen` timestamp for existing jobs
- Save all new jobs to `jobs.db`

### View database statistics

```powershell
python query_jobs.py --stats
```

Shows:
- Total jobs in database
- New jobs added today/this week
- Top 10 companies and locations

### Query jobs

```powershell
# Get jobs added today
python query_jobs.py --today

# Get jobs from last 7 days
python query_jobs.py --days 7

# Search by keyword
python query_jobs.py --search "python developer"

# Filter by location
python query_jobs.py --location "Auckland"

# Get all jobs (with limit)
python query_jobs.py --all --limit 100
```

### Export data

```powershell
# Export today's jobs to CSV
python query_jobs.py --today --export-csv today_jobs.csv

# Export search results to JSON
python query_jobs.py --search "data analyst" --export-json data_analyst_jobs.json

# Export all jobs to CSV
python query_jobs.py --all --export-csv all_jobs.csv
```

## Database Schema

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,           -- Job URL (unique identifier)
    title TEXT,                         -- Job title
    company TEXT,                       -- Company name
    location TEXT,                      -- Location
    salary TEXT,                        -- Salary (if specified)
    date_listed TEXT,                   -- Date job was listed on Seek
    job_type TEXT,                      -- Full time, Part time, Contract, etc.
    description TEXT,                   -- Job description
    first_seen TIMESTAMP,               -- When we first scraped this job
    last_seen TIMESTAMP,                -- When we last saw this job
    is_active INTEGER DEFAULT 1         -- Whether job is still active
)
```

## How Duplicates Are Handled

- Jobs are identified by their unique URL
- If a job already exists in the database:
  - The `last_seen` timestamp is updated
  - `is_active` is set to 1
  - No duplicate entry is created
- If a job is new:
  - A new record is inserted
  - `first_seen` and `last_seen` are set to current time

## Recommended Usage

**Daily scraping (2-3 times per day):**

```powershell
# Morning scrape
python seek_scraper_selenium.py

# Evening scrape
python seek_scraper_selenium.py
```

This builds your database gradually without hitting Seek's page 27 limit, since you're only scraping the last 3 days each time.

## Configuration

You can modify the scraper parameters in `seek_scraper_selenium.py` (line 986-991):

```python
jobs = scraper.scrape_search_results(
    params={
        'daterange': '3',  # Change to 1, 3, 7, 14, 31 days
        'sortmode': 'ListedDate'
    },
    max_pages=30  # Adjust based on how many pages you want to scrape
)
```

For frequent runs (2-3 times daily), `daterange='1'` or `daterange='3'` is recommended.

## Tips

1. **Start with a full scrape**: On first run, set `daterange='31'` to get the last month
2. **Then switch to incremental**: Change to `daterange='3'` for daily runs
3. **Run in headless mode**: Set `headless=True` in line 975 to run without opening browser
4. **Schedule with Task Scheduler**: Set up Windows Task Scheduler to run automatically

## Output

The scraper creates timestamped snapshot files:
- `seek_jobs_selenium_YYYYMMDD_HHMMSS.csv`
- `seek_jobs_selenium_YYYYMMDD_HHMMSS.json`

But the **master database is `jobs.db`** - use `query_jobs.py` to access all accumulated data.