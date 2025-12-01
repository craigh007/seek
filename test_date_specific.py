"""
Test specific date formats for Seek.co.nz
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta

def test_url_with_selenium(url):
    """Test a URL with Selenium and extract job count"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        time.sleep(3)

        # Look for job count indicators
        selectors = [
            "[data-automation='totalJobsCount']",
            ".fk2rw9r",  # Common job count class
            "*[class*='job']:contains('jobs')",
            "*:contains('jobs found')"
        ]

        for selector in selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text
                if 'job' in text.lower():
                    return text
            except:
                continue

        # Fallback: get page title or any text with numbers
        title = driver.title
        if 'job' in title.lower():
            return title

        return None

    except Exception as e:
        return f"Error: {e}"
    finally:
        driver.quit()

# Test different approaches
print("Testing Seek.co.nz date parameters with Selenium...")
print("-" * 60)

# Test 1: Different daterange values
date_ranges = ['1', '3', '7', '14', '31']
for dr in date_ranges:
    url = f"https://www.seek.co.nz/jobs?daterange={dr}&sortmode=ListedDate"
    print(f"\nTesting daterange={dr}:")
    print(f"URL: {url}")
    result = test_url_with_selenium(url)
    print(f"Result: {result}")

# Test 2: Check if Seek uses specific date formats
print("\n" + "="*60)
print("Testing specific date formats...")

# Common date parameter formats in job sites
today = datetime.now()
yesterday = today - timedelta(days=1)

date_formats = [
    f"dateFrom={yesterday.strftime('%Y-%m-%d')}&dateTo={today.strftime('%Y-%m-%d')}",
    f"datePosted={today.strftime('%Y-%m-%d')}",
    f"listedDate={today.strftime('%Y-%m-%d')}",
    f"fromDate={yesterday.strftime('%Y%m%d')}&toDate={today.strftime('%Y%m%d')}",
]

for date_format in date_formats:
    url = f"https://www.seek.co.nz/jobs?{date_format}&sortmode=ListedDate"
    print(f"\nTesting: {date_format}")
    print(f"URL: {url}")
    result = test_url_with_selenium(url)
    print(f"Result: {result}")