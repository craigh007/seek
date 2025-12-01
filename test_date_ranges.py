"""
Test different date range values for Seek.co.nz
"""

import requests
import re
from datetime import datetime, timedelta

def test_date_range(date_value):
    """Test a specific date range value"""
    url = f"https://www.seek.co.nz/jobs?daterange={date_value}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        # Look for job count in the response
        matches = re.findall(r'([\d,]+)\s*jobs?', response.text)
        if matches:
            # Get the first significant number (usually the total count)
            for match in matches:
                count = int(match.replace(',', ''))
                if count > 0:
                    return count
    except:
        pass
    return None

# Test common date range values
date_ranges = {
    '1': 'Last 24 hours',
    '3': 'Last 3 days',
    '7': 'Last 7 days',
    '14': 'Last 14 days',
    '30': 'Last 30 days',
    '31': 'Last 31 days',
    '60': 'Last 60 days',
    '90': 'Last 90 days',
    '999': 'Any time (test)',
    '': 'No date filter'
}

print("Testing Seek.co.nz date range parameters...")
print("-" * 50)

for value, description in date_ranges.items():
    count = test_date_range(value)
    if count:
        print(f"daterange={value:3} ({description:20}) : {count:,} jobs")
    else:
        print(f"daterange={value:3} ({description:20}) : No results/Error")

print("-" * 50)
print("\nStrategy suggestion:")
print("If we can scrape by individual days (daterange=1),")
print("we could iterate through the last 30 days individually")
print("to potentially bypass the pagination limit.")