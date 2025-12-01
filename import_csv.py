"""
Import existing CSV files into the SQLite database
"""

import csv
import sqlite3
from datetime import datetime
import argparse


def import_csv_to_db(csv_file, db_path='jobs.db'):
    """Import CSV file into the database"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    imported = 0
    skipped = 0
    errors = 0

    print(f"Importing from {csv_file}...")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Check if job already exists
                cursor.execute('SELECT id FROM jobs WHERE url = ?', (row['url'],))
                existing = cursor.fetchone()

                if existing:
                    skipped += 1
                    continue

                # Insert new job
                cursor.execute('''
                    INSERT INTO jobs (url, title, company, location, salary,
                                     date_listed, job_type, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('url'),
                    row.get('title'),
                    row.get('company'),
                    row.get('location'),
                    row.get('salary'),
                    row.get('date_listed'),
                    row.get('job_type'),
                    row.get('description')
                ))

                imported += 1

                if imported % 100 == 0:
                    print(f"  Imported {imported} jobs...")

            except Exception as e:
                errors += 1
                print(f"  Error importing row: {e}")
                continue

    conn.commit()
    conn.close()

    print(f"\nImport complete!")
    print(f"  Imported: {imported}")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"  Errors: {errors}")

    return imported, skipped, errors


def main():
    parser = argparse.ArgumentParser(description='Import CSV files into jobs database')
    parser.add_argument('csv_file', help='CSV file to import')
    parser.add_argument('--db', default='jobs.db', help='Database path (default: jobs.db)')

    args = parser.parse_args()

    import_csv_to_db(args.csv_file, args.db)


if __name__ == '__main__':
    main()