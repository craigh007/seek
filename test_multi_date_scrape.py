"""
Test multiple date range scraping strategy
"""

from seek_scraper_selenium import SeekSeleniumScraper
import time
from datetime import datetime

def test_date_ranges():
    """Test different date range values to see which work"""

    scraper = SeekSeleniumScraper(headless=True)

    # Test different date range values
    date_ranges = [1, 3, 7, 14, 31]

    results = {}

    try:
        for dr in date_ranges:
            print(f"\n{'='*50}")
            print(f"Testing daterange={dr}")
            print(f"{'='*50}")

            # Reset jobs data for each test
            scraper.jobs_data = []

            # Test with max 3 pages to see if we get different results
            jobs = scraper.scrape_search_results(
                params={
                    'daterange': str(dr),
                    'sortmode': 'ListedDate'
                },
                max_pages=3
            )

            job_count = len(jobs)
            results[dr] = job_count

            print(f"daterange={dr}: Found {job_count} jobs")

            if jobs:
                print("Sample jobs:")
                for i, job in enumerate(jobs[:3], 1):
                    print(f"  {i}. {job.get('title', 'N/A')} - {job.get('date_listed', 'N/A')}")

            # Wait between tests to be respectful
            time.sleep(5)

    finally:
        scraper.close_driver()

    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for dr, count in results.items():
        print(f"daterange={dr:2d}: {count:3d} jobs")

    return results

if __name__ == "__main__":
    test_date_ranges()