"""
Query and export jobs from the SQLite database
"""

import sqlite3
import csv
import json
from datetime import datetime, timedelta
import argparse


class JobsQuery:
    """Helper class to query the jobs database"""

    def __init__(self, db_path='jobs.db'):
        self.db_path = db_path

    def get_all_jobs(self, limit=None):
        """Get all jobs from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = 'SELECT * FROM jobs ORDER BY first_seen DESC'
        if limit:
            query += f' LIMIT {limit}'

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_new_jobs_today(self):
        """Get jobs first seen today"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM jobs
            WHERE DATE(first_seen) = DATE('now')
            ORDER BY first_seen DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_jobs_by_date_range(self, days_back=7):
        """Get jobs first seen within the last N days"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM jobs
            WHERE first_seen >= datetime('now', '-' || ? || ' days')
            ORDER BY first_seen DESC
        ''', (days_back,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def search_jobs(self, keyword):
        """Search jobs by keyword in title, company, or description"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM jobs
            WHERE title LIKE ? OR company LIKE ? OR description LIKE ?
            ORDER BY first_seen DESC
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_jobs_by_location(self, location):
        """Get jobs by location"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM jobs
            WHERE location LIKE ?
            ORDER BY first_seen DESC
        ''', (f'%{location}%',))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_statistics(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total jobs
        cursor.execute('SELECT COUNT(*) FROM jobs')
        stats['total_jobs'] = cursor.fetchone()[0]

        # Jobs added today
        cursor.execute('''
            SELECT COUNT(*) FROM jobs
            WHERE DATE(first_seen) = DATE('now')
        ''')
        stats['new_today'] = cursor.fetchone()[0]

        # Jobs added this week
        cursor.execute('''
            SELECT COUNT(*) FROM jobs
            WHERE first_seen >= datetime('now', '-7 days')
        ''')
        stats['new_this_week'] = cursor.fetchone()[0]

        # Top companies
        cursor.execute('''
            SELECT company, COUNT(*) as count
            FROM jobs
            WHERE company IS NOT NULL AND company != ''
            GROUP BY company
            ORDER BY count DESC
            LIMIT 10
        ''')
        stats['top_companies'] = cursor.fetchall()

        # Top locations
        cursor.execute('''
            SELECT location, COUNT(*) as count
            FROM jobs
            WHERE location IS NOT NULL AND location != ''
            GROUP BY location
            ORDER BY count DESC
            LIMIT 10
        ''')
        stats['top_locations'] = cursor.fetchall()

        conn.close()
        return stats

    def export_to_csv(self, jobs, filename):
        """Export jobs to CSV"""
        if not jobs:
            print("No jobs to export")
            return

        keys = jobs[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(jobs)

        print(f"Exported {len(jobs)} jobs to {filename}")

    def export_to_json(self, jobs, filename):
        """Export jobs to JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)

        print(f"Exported {len(jobs)} jobs to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Query jobs from the database')
    parser.add_argument('--all', action='store_true', help='Get all jobs')
    parser.add_argument('--today', action='store_true', help='Get jobs added today')
    parser.add_argument('--days', type=int, help='Get jobs from last N days')
    parser.add_argument('--search', type=str, help='Search jobs by keyword')
    parser.add_argument('--location', type=str, help='Filter jobs by location')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--export-csv', type=str, help='Export results to CSV file')
    parser.add_argument('--export-json', type=str, help='Export results to JSON file')
    parser.add_argument('--limit', type=int, help='Limit number of results')
    parser.add_argument('--db', type=str, default='jobs.db', help='Database path (default: jobs.db)')

    args = parser.parse_args()

    query = JobsQuery(args.db)
    jobs = []

    if args.stats:
        stats = query.get_statistics()
        print("\n=== Database Statistics ===")
        print(f"Total jobs: {stats['total_jobs']}")
        print(f"New today: {stats['new_today']}")
        print(f"New this week: {stats['new_this_week']}")

        print("\nTop 10 Companies:")
        for i, (company, count) in enumerate(stats['top_companies'], 1):
            print(f"  {i}. {company}: {count} jobs")

        print("\nTop 10 Locations:")
        for i, (location, count) in enumerate(stats['top_locations'], 1):
            print(f"  {i}. {location}: {count} jobs")
        return

    if args.today:
        jobs = query.get_new_jobs_today()
        print(f"Found {len(jobs)} jobs added today")

    elif args.days:
        jobs = query.get_jobs_by_date_range(args.days)
        print(f"Found {len(jobs)} jobs from last {args.days} days")

    elif args.search:
        jobs = query.search_jobs(args.search)
        print(f"Found {len(jobs)} jobs matching '{args.search}'")

    elif args.location:
        jobs = query.get_jobs_by_location(args.location)
        print(f"Found {len(jobs)} jobs in '{args.location}'")

    elif args.all:
        jobs = query.get_all_jobs(args.limit)
        print(f"Found {len(jobs)} jobs")

    else:
        parser.print_help()
        return

    # Display sample results
    if jobs:
        print("\n=== Sample Results (first 5) ===")
        for i, job in enumerate(jobs[:5], 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   Date Listed: {job['date_listed']}")
            print(f"   First Seen: {job['first_seen']}")
            print(f"   URL: {job['url']}")

    # Export if requested
    if jobs:
        if args.export_csv:
            query.export_to_csv(jobs, args.export_csv)

        if args.export_json:
            query.export_to_json(jobs, args.export_json)


if __name__ == '__main__':
    main()