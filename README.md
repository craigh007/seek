# Seek.co.nz Job Scraper

A Python application to extract job listings from Seek New Zealand.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
Run the scraper with default settings (scrapes recent jobs from last 31 days):

```bash
python seek_scraper.py
```

### Advanced Usage
```python
from seek_scraper import SeekScraper

scraper = SeekScraper()

# Search with specific criteria
jobs = scraper.search_jobs(
    keywords="python developer",  # Job keywords
    location="Auckland",          # Location
    date_range=7,                # Last 7 days
    max_pages=3                  # Scrape 3 pages
)

# Save results
scraper.save_to_csv("jobs.csv")
scraper.save_to_json("jobs.json")
```

## Output

The scraper extracts:
- Job title
- Company name
- Location
- Salary (if available)
- Date posted
- Job type
- Job URL
- Description snippet

Results are saved in both CSV and JSON formats.

## Rate Limiting

The scraper includes:
- 2-second delay between pages
- Retry logic with exponential backoff
- Browser-like headers to avoid detection

## Legal Notice

Please respect Seek's Terms of Service and robots.txt. This tool is for educational purposes. Consider using official APIs if available for production use.