"""
Seek.co.nz Job Scraper using Selenium
Enhanced version with browser automation to handle JavaScript and anti-bot measures
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import csv
import time
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode
import pytz
import re
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from nz_locations import get_region

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JobDatabase:
    """Supabase database manager for job listings"""

    def __init__(self, db_path=None):
        """Initialize Supabase connection (db_path ignored, kept for compatibility)"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")

        self.client = create_client(url, key)
        logger.info("Connected to Supabase")

    def insert_or_update_job(self, job):
        """Insert new job or update last_seen if it already exists

        Uses advanced duplicate detection checking:
        1. First checks by URL (exact match)
        2. Then checks by title + company + location + description snippet
        This prevents the same job with different URLs from being added
        """
        try:
            # Check if job exists by URL
            existing = self.client.table("jobs").select("id").eq("url", job['url']).execute()

            if existing.data:
                # Update last_seen timestamp
                self.client.table("jobs").update({
                    "last_seen": datetime.utcnow().isoformat(),
                    "is_active": True
                }).eq("url", job['url']).execute()
                return False  # Not new

            # Check if same job exists with different URL
            # Match by title, company, location
            desc_snippet = (job.get('description', '') or '')[:200]

            duplicate_query = self.client.table("jobs").select("id, url").eq(
                "title", job.get('title')
            ).eq(
                "company", job.get('company')
            ).eq(
                "location", job.get('location')
            ).execute()

            # Check description match in Python (Supabase doesn't have SUBSTR)
            for dup in duplicate_query.data:
                dup_full = self.client.table("jobs").select("description").eq("id", dup["id"]).execute()
                if dup_full.data:
                    dup_desc = (dup_full.data[0].get("description", "") or "")[:200]
                    if dup_desc == desc_snippet:
                        logger.info(f"Duplicate job detected (different URL): {job.get('title')} @ {job.get('company')}")
                        logger.info(f"  Existing URL: {dup['url'][:80]}...")
                        logger.info(f"  New URL:      {job['url'][:80]}...")
                        self.client.table("jobs").update({
                            "last_seen": datetime.utcnow().isoformat(),
                            "is_active": True
                        }).eq("id", dup["id"]).execute()
                        return False  # Not new (duplicate with different URL)

            # Insert new job
            now = datetime.utcnow().isoformat()
            location = job.get('location', '')
            region = get_region(location)

            self.client.table("jobs").insert({
                "url": job.get('url'),
                "title": job.get('title'),
                "company": job.get('company'),
                "location": location,
                "region": region,
                "salary": job.get('salary'),
                "date_listed": job.get('date_listed'),
                "job_type": job.get('job_type'),
                "description": job.get('description'),
                "first_seen": now,
                "last_seen": now,
                "is_active": True
            }).execute()
            logger.debug(f"Inserted job in region: {region}")
            return True  # New job

        except Exception as e:
            logger.error(f"Error inserting/updating job: {e}")
            return False

    def get_job_count(self):
        """Get total number of jobs in database"""
        result = self.client.table("jobs").select("id", count="exact").execute()
        return result.count or 0

    def get_new_jobs_today(self):
        """Get count of jobs first seen today"""
        today = datetime.utcnow().strftime('%Y-%m-%d')
        result = self.client.table("jobs").select("id", count="exact").gte(
            "first_seen", f"{today}T00:00:00"
        ).execute()
        return result.count or 0

    def export_to_csv(self, filename=None):
        """Export all jobs to CSV"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'seek_jobs_export_{timestamp}.csv'

        result = self.client.table("jobs").select("*").order("first_seen", desc=True).execute()
        rows = result.data

        if not rows:
            logger.warning("No jobs to export")
            return filename

        columns = rows[0].keys()

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Exported {len(rows)} jobs to {filename}")
        return filename


class SeekSeleniumScraper:
    def __init__(self, headless=False, db_path='jobs.db'):
        self.base_url = "https://www.seek.co.nz"
        self.search_url = f"{self.base_url}/jobs"
        self.jobs_data = []
        self.headless = headless
        self.driver = None
        self.db = JobDatabase(db_path)

    def clean_text(self, text):
        """Clean text to fix encoding and formatting issues"""
        if not text:
            return text

        # More comprehensive encoding fixes
        encoding_fixes = {
            'â€"': '-',     # Fix corrupted em dash to regular dash
            '—': '-',       # Replace em dash with regular dash
            '–': '-',       # Replace en dash with regular dash
            'â€™': "'",     # Fix apostrophe
            'â€œ': '"',     # Fix opening quote
            'â€': '"',      # Fix closing quote
            'Â£': '£',      # Fix pound symbol
            'Â': '',        # Remove standalone Â characters
            'â€¢': '•',     # Fix bullet point
            'â€¦': '...',   # Fix ellipsis
            'â€': '€',      # Fix euro symbol
            'Ã©': 'é',      # Fix accented e
            'Ã¡': 'á',      # Fix accented a
            'Ã­': 'í',      # Fix accented i
            'Ã³': 'ó',      # Fix accented o
            'Ãº': 'ú',      # Fix accented u
        }

        # Apply all encoding fixes
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)

        # Clean up whitespace
        text = ' '.join(text.split())  # Remove extra whitespace
        text = text.strip()

        return text

    def parse_relative_date(self, date_text):
        """Convert relative date text to actual NZ date format"""
        if not date_text:
            return "Date not found"

        # Set up NZ timezone
        nz_tz = pytz.timezone('Pacific/Auckland')
        now = datetime.now(nz_tz)

        # Clean the text first
        date_text_clean = date_text.lower().strip()

        # Remove "listed" or "posted" prefixes
        date_text_clean = re.sub(r'^(listed|posted)\s+', '', date_text_clean)

        try:
            # Handle specific patterns
            if date_text_clean == 'today':
                return now.strftime('%d/%m/%Y')
            elif date_text_clean == 'yesterday':
                return (now - timedelta(days=1)).strftime('%d/%m/%Y')
            elif date_text_clean == 'just now':
                return now.strftime('%d/%m/%Y')

            # Handle "X hours ago"
            hours_match = re.match(r'(\d+)\s*hours?\s*ago', date_text_clean)
            if hours_match:
                hours = int(hours_match.group(1))
                return (now - timedelta(hours=hours)).strftime('%d/%m/%Y')

            # Handle "X minutes ago"
            mins_match = re.match(r'(\d+)\s*(mins?|minutes?)\s*ago', date_text_clean)
            if mins_match:
                minutes = int(mins_match.group(1))
                return (now - timedelta(minutes=minutes)).strftime('%d/%m/%Y')

            # Handle "X days ago"
            days_match = re.match(r'(\d+)\s*days?\s*ago', date_text_clean)
            if days_match:
                days = int(days_match.group(1))
                return (now - timedelta(days=days)).strftime('%d/%m/%Y')

            # Handle "X weeks ago"
            weeks_match = re.match(r'(\d+)\s*weeks?\s*ago', date_text_clean)
            if weeks_match:
                weeks = int(weeks_match.group(1))
                return (now - timedelta(weeks=weeks)).strftime('%d/%m/%Y')

            # Handle "X months ago"
            months_match = re.match(r'(\d+)\s*months?\s*ago', date_text_clean)
            if months_match:
                months = int(months_match.group(1))
                return (now - timedelta(days=months*30)).strftime('%d/%m/%Y')

            # Handle specific hour text patterns like "six hours ago"
            hour_words = {
                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                'eleven': 11, 'twelve': 12
            }

            for word, num in hour_words.items():
                if f'{word} hour' in date_text_clean:
                    return (now - timedelta(hours=num)).strftime('%d/%m/%Y')

            # If we can't parse it, return the cleaned original text
            return self.clean_text(date_text)

        except Exception as e:
            logger.debug(f"Error parsing date '{date_text}': {e}")
            return self.clean_text(date_text)

    def setup_driver(self):
        """Setup Chrome driver with anti-detection options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Anti-detection settings
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome driver setup successful")
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            logger.info("Please ensure Chrome and chromedriver are installed")
            raise

    def close_driver(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            logger.info("Driver closed")

    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None

    def scrape_job_details(self, job_url):
        """Navigate to job page and scrape full description"""
        try:
            # Store current URL to return later
            current_url = self.driver.current_url

            # Navigate to job page
            self.driver.get(job_url)
            time.sleep(2)  # Wait for page load

            full_description = ""

            # Try multiple selectors for job description
            desc_selectors = [
                "[data-automation='jobAdDetails']",
                "[data-automation='jobDescription']",
                "[data-testid='job-details-content']",
                ".job-details-content",
                "div[class*='jobDescription']",
                "div[class*='job-description']",
                "section[aria-label='Job description']",
                "div[data-automation='jobDetailsContent']",
            ]

            for selector in desc_selectors:
                try:
                    desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if desc_elem:
                        full_description = desc_elem.text.strip()
                        if len(full_description) > 100:  # Looks like real content
                            break
                except:
                    continue

            # Fallback: try to get main content area
            if not full_description or len(full_description) < 100:
                try:
                    # Look for the main job content wrapper
                    main_content = self.driver.find_element(By.CSS_SELECTOR, "main")
                    if main_content:
                        # Get all paragraph text
                        paragraphs = main_content.find_elements(By.TAG_NAME, "p")
                        desc_parts = [p.text.strip() for p in paragraphs if p.text.strip()]
                        if desc_parts:
                            full_description = "\n".join(desc_parts)
                except:
                    pass

            # Also try to get additional details like requirements, benefits
            extra_sections = []
            section_selectors = [
                "[data-automation='job-detail-requirements']",
                "[data-automation='job-detail-benefits']",
                "ul[class*='requirement']",
                "ul[class*='benefit']",
            ]

            for selector in section_selectors:
                try:
                    section = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if section and section.text.strip():
                        extra_sections.append(section.text.strip())
                except:
                    continue

            if extra_sections:
                full_description += "\n\n" + "\n".join(extra_sections)

            # Clean the description
            full_description = self.clean_text(full_description)

            # Navigate back to search results
            self.driver.get(current_url)
            time.sleep(2)

            return full_description if full_description else None

        except Exception as e:
            logger.error(f"Error scraping job details from {job_url}: {e}")
            # Try to go back to search
            try:
                self.driver.back()
                time.sleep(2)
            except:
                pass
            return None

    def parse_job_card(self, card_element):
        """Extract job details from a job card element"""
        job = {}

        try:
            # Job title and URL
            try:
                title_link = card_element.find_element(By.CSS_SELECTOR, "a[data-automation='jobTitle']")
                job['title'] = self.clean_text(title_link.text.strip())
                job['url'] = title_link.get_attribute('href')
            except:
                try:
                    title_link = card_element.find_element(By.CSS_SELECTOR, "h3 a")
                    job['title'] = self.clean_text(title_link.text.strip())
                    job['url'] = title_link.get_attribute('href')
                except:
                    # Try any link in the card
                    try:
                        title_link = card_element.find_element(By.CSS_SELECTOR, "a[href*='/job/']")
                        job['title'] = self.clean_text(title_link.text.strip())
                        job['url'] = title_link.get_attribute('href')
                    except:
                        pass

            # Company
            try:
                company = card_element.find_element(By.CSS_SELECTOR, "[data-automation='jobCompany']")
                job['company'] = self.clean_text(company.text.strip())
            except:
                try:
                    company = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-advertiser']")
                    job['company'] = self.clean_text(company.text.strip())
                except:
                    # Try alternative selectors for company
                    try:
                        company = card_element.find_element(By.CSS_SELECTOR, "span[title]")
                        if "company" in company.get_attribute('title').lower():
                            job['company'] = self.clean_text(company.text.strip())
                    except:
                        pass

            # Location
            try:
                location = card_element.find_element(By.CSS_SELECTOR, "[data-automation='jobLocation']")
                job['location'] = self.clean_text(location.text.strip())
            except:
                try:
                    location = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-location']")
                    job['location'] = self.clean_text(location.text.strip())
                except:
                    # Try alternative location selectors
                    location_selectors = [
                        "span[data-automation*='location']",
                        "div[data-automation*='location']",
                        "span:contains('Auckland')",
                        "span:contains('Wellington')",
                        "span:contains('Christchurch')"
                    ]
                    for selector in location_selectors:
                        try:
                            location = card_element.find_element(By.CSS_SELECTOR, selector)
                            if location.text.strip():
                                job['location'] = self.clean_text(location.text.strip())
                                break
                        except:
                            continue

            # Salary
            try:
                salary = card_element.find_element(By.CSS_SELECTOR, "[data-automation='jobSalary']")
                job['salary'] = self.clean_text(salary.text.strip())
            except:
                try:
                    salary = card_element.find_element(By.CSS_SELECTOR, "[data-testid='job-card-salary']")
                    job['salary'] = self.clean_text(salary.text.strip())
                except:
                    # Try finding salary by looking for currency symbols or salary-related text
                    salary_selectors = [
                        "span:contains('$')",
                        "div:contains('$')",
                        "span[data-automation*='salary']",
                        "div[data-automation*='salary']",
                        "span:contains('per hour')",
                        "span:contains('per year')",
                        "span:contains('Competitive')",
                        "span:contains('DOE')"
                    ]
                    for selector in salary_selectors:
                        try:
                            salary_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                            salary_text = self.clean_text(salary_elem.text.strip())
                            if any(keyword in salary_text.lower() for keyword in ['$', 'salary', 'competitive', 'doe', 'per hour', 'per year']):
                                job['salary'] = salary_text
                                break
                        except:
                            continue

                    if 'salary' not in job:
                        job['salary'] = "Not specified"

            # Enhanced Date posted extraction
            date_found = False
            try:
                # Get all text from the card
                all_card_text = card_element.text

                # Enhanced regex patterns for dates (case insensitive)
                date_patterns = [
                    r'listed\s+(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+hours?\s+ago',  # "Listed Six Hours Ago"
                    r'\d+\s*hours?\s*ago',       # "2 hours ago", "1 hour ago"
                    r'\d+\s*mins?\s*ago',        # "30 mins ago", "5 min ago"
                    r'\d+\s*minutes?\s*ago',     # "30 minutes ago"
                    r'\d+\s*days?\s*ago',        # "2 days ago", "1 day ago"
                    r'\d+\s*weeks?\s*ago',       # "1 week ago", "2 weeks ago"
                    r'\d+\s*months?\s*ago',      # "1 month ago"
                    r'today',                    # "today"
                    r'yesterday',                # "yesterday"
                    r'just\s*now',              # "just now"
                    r'posted\s*\d+\s*hours?\s*ago',     # "posted 2 hours ago"
                    r'posted\s*\d+\s*days?\s*ago',      # "posted 2 days ago"
                    r'posted\s*today',                   # "posted today"
                    r'posted\s*yesterday',               # "posted yesterday"
                    r'listed\s*\d+\s*hours?\s*ago',     # "listed 2 hours ago"
                    r'listed\s*\d+\s*days?\s*ago',      # "listed 2 days ago"
                    r'listed\s*today',                   # "listed today"
                ]

                # Search for date patterns with case insensitive matching
                for pattern in date_patterns:
                    match = re.search(pattern, all_card_text, re.IGNORECASE)
                    if match:
                        # Use the new parse_relative_date method to convert to NZ date format
                        job['date_listed'] = self.parse_relative_date(match.group().strip())
                        date_found = True
                        break

                # If no pattern found, try more aggressive text search
                if not date_found:
                    # Split text into lines and look for date-like content
                    lines = all_card_text.split('\n')
                    for line in lines:
                        line = line.strip().lower()
                        if line and len(line) < 50:  # Date lines are usually short
                            # Look for time-related keywords
                            time_keywords = ['ago', 'today', 'yesterday', 'hour', 'day', 'week', 'month', 'min', 'posted', 'listed']
                            if any(keyword in line for keyword in time_keywords):
                                # Exclude location names
                                location_keywords = ['auckland', 'wellington', 'christchurch', 'hamilton', 'wanaka', 'otago', 'tauranga', 'dunedin']
                                if not any(location in line for location in location_keywords):
                                    job['date_listed'] = self.parse_relative_date(line)
                                    date_found = True
                                    break

                # Try specific selectors as fallback
                if not date_found:
                    date_selectors = [
                        "[data-automation='jobListingDate']",
                        "[data-testid='job-listing-date']",
                        "time",
                        "span[data-automation*='date']",
                        "div[data-automation*='date']",
                        "*[title*='ago']",
                        "*[title*='today']",
                        "*[title*='yesterday']"
                    ]

                    for selector in date_selectors:
                        try:
                            date_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                            date_text = date_elem.text.strip()
                            title_attr = date_elem.get_attribute('title') or ''

                            # Check both text content and title attribute
                            for text_to_check in [date_text, title_attr]:
                                if text_to_check:
                                    text_lower = text_to_check.lower()
                                    # Validate it's actually a date, not location data
                                    location_keywords = ['auckland', 'wellington', 'christchurch', 'hamilton', 'wanaka', 'otago']
                                    if not any(city in text_lower for city in location_keywords):
                                        time_keywords = ['ago', 'day', 'hour', 'week', 'month', 'posted', 'today', 'yesterday', 'min']
                                        if any(keyword in text_lower for keyword in time_keywords):
                                            job['date_listed'] = self.parse_relative_date(text_to_check)
                                            date_found = True
                                            break

                            if date_found:
                                break
                        except:
                            continue

                if not date_found:
                    job['date_listed'] = "Date not found"

            except Exception as e:
                logger.error(f"Error in date extraction: {e}")
                job['date_listed'] = "Date extraction error"

            # Enhanced Job type extraction
            try:
                # First check all text content for job type keywords
                all_card_text = card_element.text
                job_type_found = False

                # Look for job type patterns in text using regex
                job_type_patterns = [
                    r'full[\s-]?time',
                    r'part[\s-]?time',
                    r'contract(?:/temp)?',
                    r'temporary',
                    r'casual',
                    r'permanent',
                    r'freelance',
                    r'internship'
                ]

                for pattern in job_type_patterns:
                    match = re.search(pattern, all_card_text.lower())
                    if match:
                        matched_text = match.group()
                        # Clean up the matched text
                        if 'full' in matched_text:
                            job['job_type'] = "Full time"
                        elif 'part' in matched_text:
                            job['job_type'] = "Part time"
                        elif 'contract' in matched_text:
                            job['job_type'] = "Contract"
                        elif 'temp' in matched_text:
                            job['job_type'] = "Temporary"
                        elif 'casual' in matched_text:
                            job['job_type'] = "Casual"
                        elif 'permanent' in matched_text:
                            job['job_type'] = "Permanent"
                        elif 'freelance' in matched_text:
                            job['job_type'] = "Freelance"
                        elif 'internship' in matched_text:
                            job['job_type'] = "Internship"

                        job_type_found = True
                        break

                # Try specific selectors if pattern matching didn't work
                if not job_type_found:
                    job_type_selectors = [
                        "[data-automation='job-card-work-type']",
                        "[data-testid='job-card-work-type']",
                        "[data-automation*='work-type']",
                        "[data-testid*='work-type']"
                    ]

                    for selector in job_type_selectors:
                        try:
                            job_type_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                            job_type_text = job_type_elem.text.strip()
                            if job_type_text and len(job_type_text) < 50:  # Reasonable length for job type
                                job['job_type'] = job_type_text
                                job_type_found = True
                                break
                        except:
                            continue

                if not job_type_found:
                    job['job_type'] = "Type not specified"

            except Exception as e:
                job['job_type'] = "Type extraction error"

            # Enhanced Description extraction
            try:
                description_found = False

                # First try specific description selectors
                desc_selectors = [
                    "[data-automation='jobShortDescription']",
                    "[data-testid='job-short-description']",
                    "[data-automation*='description']",
                    "[data-testid*='description']",
                    ".job-description",
                    ".job-snippet"
                ]

                for selector in desc_selectors:
                    try:
                        desc_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                        desc_text = desc_elem.text.strip()
                        # Only use if it's substantial text and not just metadata
                        if (len(desc_text) > 30 and
                            desc_text not in [job.get('title', ''), job.get('company', ''), job.get('location', '')] and
                            not desc_text.startswith('This is a ') and  # Filter out our job type descriptions
                            'full time' not in desc_text.lower() and
                            'part time' not in desc_text.lower() and
                            'contract' not in desc_text.lower()):

                            clean_desc = self.clean_text(desc_text)
                            job['description'] = clean_desc[:400] + "..." if len(clean_desc) > 400 else clean_desc
                            description_found = True
                            break
                    except:
                        continue

                # Try to extract meaningful description from all text
                if not description_found:
                    try:
                        all_text = card_element.text
                        lines = [line.strip() for line in all_text.split('\n') if line.strip()]

                        # Define comprehensive filter terms
                        filter_terms = [
                            job.get('title', ''),
                            job.get('company', ''),
                            job.get('location', ''),
                            job.get('salary', ''),
                            job.get('job_type', ''),
                            'ago', 'day', 'hour', 'week', 'month', 'posted',
                            'apply', 'save', 'favourite', 'featured',
                            'full time', 'part time', 'contract', 'temporary',
                            'auckland', 'wellington', 'christchurch', 'hamilton'
                        ]

                        # Look for lines that seem like job descriptions
                        description_lines = []
                        for line in lines:
                            line_lower = line.lower()
                            # Skip short lines and filter terms
                            if len(line) < 20:
                                continue

                            # Skip if line matches any filter terms
                            if any(term.lower() in line_lower for term in filter_terms if term and len(term) > 2):
                                continue

                            # Skip lines that are just job metadata
                            if any(keyword in line_lower for keyword in ['listed', 'posted', 'viewed', 'saved']):
                                continue

                            # This looks like a description line
                            description_lines.append(line)

                            # Stop after we get a good amount of description
                            if len(' '.join(description_lines)) > 200:
                                break

                        if description_lines:
                            description = ' '.join(description_lines[:3])  # Take first 3 meaningful lines
                            # Clean up the description
                            description = re.sub(r'\s+', ' ', description)  # Remove extra whitespace
                            description = self.clean_text(description)  # Fix encoding issues
                            job['description'] = description[:400] + "..." if len(description) > 400 else description
                            description_found = True

                    except Exception as e:
                        logger.debug(f"Error in description extraction: {e}")

                if not description_found:
                    job['description'] = "Description not available"

            except Exception as e:
                job['description'] = "Description extraction error"

            return job if job.get('title') else None

        except Exception as e:
            logger.error(f"Error parsing job card: {e}")
            return None

    def scrape_page(self):
        """Scrape jobs from current page"""
        jobs = []

        # Wait for page to load
        time.sleep(3)

        # Try multiple selectors for job cards
        selectors = [
            "article[data-testid*='job-card']",
            "article",
            "div[data-automation='normalJob']",
            "div[data-testid='job-card']",
            "[data-card-type='JobCard']"
        ]

        job_cards = []
        for selector in selectors:
            try:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if job_cards:
                    logger.info(f"Found {len(job_cards)} job cards using selector: {selector}")
                    break
            except:
                continue

        if not job_cards:
            logger.warning("No job cards found on page")
            return jobs

        for card in job_cards:
            job = self.parse_job_card(card)
            if job:
                jobs.append(job)
                logger.info(f"Scraped: {job.get('title', 'Unknown')}")

        return jobs

    def scrape_search_results(self, params=None, max_pages=3):
        """Scrape job listings from search results"""
        if not self.driver:
            self.setup_driver()

        if params is None:
            params = {
                # No daterange = all available jobs
                'sortmode': 'ListedDate'
            }

        # Build URL
        url = f"{self.search_url}?{urlencode(params)}"
        logger.info(f"Starting scrape from: {url}")

        # Load initial page
        self.driver.get(url)

        # Wait for initial load
        time.sleep(5)

        # Check if we need to handle any popups or cookies
        try:
            # Try to close any cookie banners
            cookie_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept')]")
            cookie_button.click()
            time.sleep(1)
        except:
            pass

        page = 1
        total_jobs = 0

        while page <= max_pages:
            logger.info(f"Scraping page {page}")

            # Scrape current page (basic info from cards)
            page_jobs = self.scrape_page()

            # Save to database and track new vs existing
            new_jobs = 0
            for job in page_jobs:
                job_url = job.get('url')
                if not job_url:
                    continue

                # Check if job already exists in database
                existing = self.db.client.table("jobs").select("id, description").eq("url", job_url).execute()

                if existing.data:
                    existing_job = existing.data[0]
                    existing_desc = existing_job.get('description') or ''

                    # Check if we need to backfill the full description
                    # (short descriptions or snippets ending with "..." need updating)
                    needs_backfill = (
                        len(existing_desc) < 500 or
                        existing_desc.endswith('...') or
                        'Description not available' in existing_desc
                    )

                    if needs_backfill:
                        logger.info(f"Backfilling description for: {job.get('title', 'Unknown')}")
                        full_description = self.scrape_job_details(job_url)

                        if full_description and len(full_description) > len(existing_desc):
                            self.db.client.table("jobs").update({
                                "description": full_description,
                                "last_seen": datetime.utcnow().isoformat(),
                                "is_active": True
                            }).eq("id", existing_job['id']).execute()
                            logger.info(f"  Updated with {len(full_description)} chars")
                        else:
                            # Just update last_seen
                            self.db.client.table("jobs").update({
                                "last_seen": datetime.utcnow().isoformat(),
                                "is_active": True
                            }).eq("id", existing_job['id']).execute()
                    else:
                        # Job exists with full description - just update last_seen
                        self.db.client.table("jobs").update({
                            "last_seen": datetime.utcnow().isoformat(),
                            "is_active": True
                        }).eq("url", job_url).execute()
                        logger.debug(f"Updated existing: {job.get('title', 'Unknown')}")
                else:
                    # New job - scrape full details before inserting
                    logger.info(f"New job found, scraping details: {job.get('title', 'Unknown')}")
                    full_description = self.scrape_job_details(job_url)

                    if full_description:
                        job['description'] = full_description
                        logger.info(f"  Got {len(full_description)} chars of description")

                    # Now insert with full details
                    if self.db.insert_or_update_job(job):
                        new_jobs += 1

            self.jobs_data.extend(page_jobs)
            total_jobs += len(page_jobs)

            logger.info(f"Page {page}: Found {len(page_jobs)} jobs ({new_jobs} new). Total scraped: {total_jobs}")

            if page < max_pages:
                # Try to go to next page
                try:
                    # Scroll to bottom to ensure pagination elements are loaded
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)

                    # Scroll back up a bit to see pagination
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 500);")
                    time.sleep(2)

                    # Comprehensive list of next button selectors
                    next_selectors = [
                        "a[data-automation='page-next']",
                        "button[data-automation='page-next']",
                        "a[aria-label='Next page']",
                        "button[aria-label='Next page']",
                        "a[aria-label='Next']",
                        "button[aria-label='Next']",
                        "a[title='Next page']",
                        "button[title='Next page']",
                        "a.pagination-next",
                        "button.pagination-next",
                        "a:contains('Next')",
                        "button:contains('Next')",
                        "a[href*='page=2']" if page == 1 else f"a[href*='page={page+1}']",
                        "nav a:last-child",
                        "[data-testid='pagination-next']",
                        ".pagination-container a:last-child"
                    ]

                    next_clicked = False
                    next_button = None

                    # First try to find any next button
                    for selector in next_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    # Check if it's not disabled
                                    classes = element.get_attribute('class') or ''
                                    if 'disabled' not in classes.lower():
                                        next_button = element
                                        logger.info(f"Found next button with selector: {selector}")
                                        break
                            if next_button:
                                break
                        except Exception as e:
                            logger.debug(f"Selector {selector} failed: {e}")
                            continue

                    # If no next button found, try XPath selectors
                    if not next_button:
                        xpath_selectors = [
                            "//a[contains(text(), 'Next')]",
                            "//button[contains(text(), 'Next')]",
                            "//a[contains(@aria-label, 'Next')]",
                            "//button[contains(@aria-label, 'Next')]",
                            "//a[contains(@title, 'Next')]",
                            "//button[contains(@title, 'Next')]",
                            f"//a[contains(@href, 'page={page+1}')]",
                            "//nav//a[last()]",
                            "//*[@data-automation='page-next']",
                            "//*[contains(@class, 'pagination')]//a[last()]"
                        ]

                        for xpath in xpath_selectors:
                            try:
                                elements = self.driver.find_elements(By.XPATH, xpath)
                                for element in elements:
                                    if element.is_displayed() and element.is_enabled():
                                        classes = element.get_attribute('class') or ''
                                        if 'disabled' not in classes.lower():
                                            next_button = element
                                            logger.info(f"Found next button with XPath: {xpath}")
                                            break
                                if next_button:
                                    break
                            except Exception as e:
                                logger.debug(f"XPath {xpath} failed: {e}")
                                continue

                    # Try to click the next button
                    if next_button:
                        try:
                            # Scroll the button into view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                            time.sleep(1)

                            # Try regular click first
                            next_button.click()
                            next_clicked = True
                            logger.info(f"Successfully clicked next button for page {page + 1}")

                        except Exception as click_error:
                            logger.info(f"Regular click failed: {click_error}")
                            try:
                                # Try JavaScript click as fallback
                                self.driver.execute_script("arguments[0].click();", next_button)
                                next_clicked = True
                                logger.info(f"Successfully clicked next button with JavaScript for page {page + 1}")
                            except Exception as js_error:
                                logger.error(f"JavaScript click also failed: {js_error}")

                        if next_clicked:
                            # Wait for page to load
                            time.sleep(5)

                            # Wait for new content to load by checking if URL changed or new jobs appeared
                            start_time = time.time()
                            while time.time() - start_time < 10:  # 10 second timeout
                                try:
                                    current_url = self.driver.current_url
                                    if f'page={page+1}' in current_url:
                                        logger.info(f"Successfully navigated to page {page + 1}")
                                        break
                                    time.sleep(1)
                                except:
                                    break

                    if not next_clicked:
                        logger.info("No next button found or unable to click it")

                        # Check if we can construct next page URL manually
                        current_url = self.driver.current_url
                        if 'page=' in current_url:
                            # Replace existing page parameter
                            next_url = re.sub(r'page=\d+', f'page={page+1}', current_url)
                        else:
                            # Add page parameter
                            separator = '&' if '?' in current_url else '?'
                            next_url = f"{current_url}{separator}page={page+1}"

                        logger.info(f"Trying direct navigation to: {next_url}")
                        self.driver.get(next_url)
                        time.sleep(5)

                        # Check if we got valid content
                        test_jobs = self.scrape_page()
                        if test_jobs:
                            logger.info(f"Direct navigation successful, found {len(test_jobs)} jobs")
                            # We'll scrape this page in the next iteration
                            continue
                        else:
                            logger.info("Direct navigation failed - no more pages")
                            break

                except Exception as e:
                    logger.error(f"Error during pagination: {e}")
                    break

            page += 1

        return self.jobs_data

    def save_to_csv(self, filename=None):
        """Save scraped jobs to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'seek_jobs_selenium_{timestamp}.csv'

        if not self.jobs_data:
            logger.warning("No data to save")
            return

        # Get all unique keys
        all_keys = set()
        for job in self.jobs_data:
            all_keys.update(job.keys())

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(self.jobs_data)

        logger.info(f"Saved {len(self.jobs_data)} jobs to {filename}")
        return filename

    def save_to_json(self, filename=None):
        """Save scraped jobs to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'seek_jobs_selenium_{timestamp}.json'

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.jobs_data)} jobs to {filename}")
        return filename


def main():
    """Main function to run the scraper"""
    print("=" * 60)
    print("Seek.co.nz Job Scraper (SQLite Database Version)")
    print("=" * 60)
    print("\nThis scraper requires Chrome browser and chromedriver.")
    print("If not installed, please download from:")
    print("https://chromedriver.chromium.org/")
    print("=" * 60)

    scraper = SeekSeleniumScraper(headless=False)  # Set to True for headless mode

    # Show current database stats
    total_in_db = scraper.db.get_job_count()
    new_today = scraper.db.get_new_jobs_today()
    print(f"\nDatabase Stats:")
    print(f"  Total jobs in database: {total_in_db}")
    print(f"  New jobs added today: {new_today}")

    try:
        print("\nStarting scraper (all available jobs)...")
        print("Note: Seek limits to ~27 pages. Run daily to capture all new jobs.")
        jobs = scraper.scrape_search_results(
            params={
                # No daterange = all available jobs (limited by Seek's pagination)
                'sortmode': 'ListedDate'
            },
            max_pages=30  # Scrape up to 30 pages (will stop at page 27 limit or when no more pages)
        )

        if jobs:
            print(f"\nSuccessfully scraped {len(jobs)} jobs!")

            # Show updated database stats
            total_in_db = scraper.db.get_job_count()
            new_today = scraper.db.get_new_jobs_today()
            print(f"\nUpdated Database Stats:")
            print(f"  Total jobs in database: {total_in_db}")
            print(f"  New jobs added today: {new_today}")

            print("\nSample of scraped jobs:")
            print("-" * 50)

            for i, job in enumerate(jobs[:5], 1):
                print(f"\n{i}. {job.get('title', 'N/A')}")
                print(f"   Company: {job.get('company', 'N/A')}")
                print(f"   Location: {job.get('location', 'N/A')}")
                print(f"   Salary: {job.get('salary', 'Not specified')}")
                print(f"   Posted: {job.get('date_listed', 'N/A')}")

            # Optional: Save timestamped snapshot files
            csv_file = scraper.save_to_csv()
            json_file = scraper.save_to_json()

            print(f"\nSnapshot files saved:")
            print(f"  - CSV: {csv_file}")
            print(f"  - JSON: {json_file}")
            print(f"\nNote: All jobs are automatically saved to jobs.db")
        else:
            print("\nNo jobs were scraped.")
            print("Possible reasons:")
            print("- Website structure has changed")
            print("- Anti-bot protection is blocking access")
            print("- Network issues")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nPlease ensure:")
        print("1. Chrome browser is installed")
        print("2. ChromeDriver is installed and in PATH")
        print("3. You have internet connection")

    finally:
        scraper.close_driver()
        print("\nScraper finished.")


if __name__ == "__main__":
    main()