"""
Advanced duplicate detection using multiple fields
Identifies jobs that are truly the same despite having different URLs
"""

import sqlite3
from datetime import datetime

def find_duplicates():
    """Find duplicate jobs based on title, company, location, and description"""
    conn = sqlite3.connect('jobs.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("ADVANCED DUPLICATE DETECTION")
    print("=" * 80)
    print("\nSearching for jobs with identical:")
    print("  - Title")
    print("  - Company")
    print("  - Location")
    print("  - Description (first 200 chars)")
    print()

    # Find duplicates based on multiple fields
    cursor.execute('''
        SELECT
            title,
            company,
            location,
            SUBSTR(description, 1, 200) as desc_snippet,
            COUNT(*) as count,
            GROUP_CONCAT(id) as ids,
            GROUP_CONCAT(url, ' | ') as urls,
            GROUP_CONCAT(date_listed, ' | ') as dates,
            MIN(first_seen) as earliest,
            MAX(first_seen) as latest
        FROM jobs
        WHERE title IS NOT NULL
          AND company IS NOT NULL
          AND location IS NOT NULL
        GROUP BY title, company, location, SUBSTR(description, 1, 200)
        HAVING count > 1
        ORDER BY count DESC
    ''')

    duplicates = cursor.fetchall()

    print(f"Found {len(duplicates)} groups of duplicate jobs")
    print()

    if not duplicates:
        print("No duplicates found!")
        conn.close()
        return []

    total_dupes = sum(row['count'] - 1 for row in duplicates)  # -1 because we keep one
    print(f"Total duplicate entries: {total_dupes}")
    print(f"(We'll keep the oldest entry from each group)")
    print()

    duplicate_groups = []

    for i, row in enumerate(duplicates, 1):
        print(f"\n{'=' * 80}")
        print(f"Duplicate Group #{i} - {row['count']} identical jobs")
        print(f"{'=' * 80}")

        print(f"Title:    {row['title']}")
        print(f"Company:  {row['company']}")
        print(f"Location: {row['location']}")
        print(f"Description snippet: {row['desc_snippet'][:100]}...")
        print()

        # Get full details of each duplicate
        ids = [int(x) for x in row['ids'].split(',')]

        print(f"Job IDs in this group: {ids}")
        print()

        for job_id in ids:
            cursor.execute('''
                SELECT id, url, date_listed, first_seen, triage_status
                FROM jobs
                WHERE id = ?
            ''', (job_id,))

            job = cursor.fetchone()

            triage = job['triage_status'] or 'untagged'
            print(f"  ID {job['id']:4d} | First seen: {job['first_seen']} | "
                  f"Date listed: {job['date_listed']:20s} | Triage: {triage:10s}")
            print(f"           URL: {job['url'][:80]}...")

        duplicate_groups.append({
            'ids': ids,
            'count': row['count'],
            'title': row['title'],
            'company': row['company'],
            'location': row['location']
        })

    conn.close()
    return duplicate_groups


def remove_duplicates(dry_run=True):
    """Remove duplicate entries, keeping the oldest one (earliest first_seen)"""
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()

    print("\n" + "=" * 80)
    if dry_run:
        print("DRY RUN - Finding which duplicates would be removed")
    else:
        print("REMOVING DUPLICATES - Keeping oldest entry from each group")
    print("=" * 80)
    print()

    # Find duplicates and their IDs ordered by first_seen
    cursor.execute('''
        SELECT
            title,
            company,
            location,
            SUBSTR(description, 1, 200) as desc_snippet,
            GROUP_CONCAT(id ORDER BY first_seen ASC) as ids,
            COUNT(*) as count
        FROM jobs
        WHERE title IS NOT NULL
          AND company IS NOT NULL
          AND location IS NOT NULL
        GROUP BY title, company, location, SUBSTR(description, 1, 200)
        HAVING count > 1
    ''')

    duplicate_groups = cursor.fetchall()

    total_removed = 0

    for row in duplicate_groups:
        ids = [int(x) for x in row[4].split(',')]  # ids column
        keep_id = ids[0]  # Keep the first one (oldest by first_seen)
        remove_ids = ids[1:]  # Remove the rest

        print(f"Group: {row[0]} @ {row[1]} - {row[2]}")
        print(f"  Keeping ID: {keep_id}")
        print(f"  Removing IDs: {remove_ids}")

        if not dry_run:
            for remove_id in remove_ids:
                cursor.execute('DELETE FROM jobs WHERE id = ?', (remove_id,))
                total_removed += 1
                print(f"    Deleted ID {remove_id}")
        else:
            print(f"    Would delete {len(remove_ids)} entries")

        print()

    if not dry_run:
        conn.commit()
        print(f"\nTotal entries removed: {total_removed}")
    else:
        print(f"\nTotal entries that would be removed: {sum(len(row[4].split(',')) - 1 for row in duplicate_groups)}")

    conn.close()
    return total_removed


def main():
    print("\n" + "=" * 80)
    print("SEEK JOBS - TRUE DUPLICATE FINDER")
    print("=" * 80)
    print()

    # Step 1: Find duplicates
    duplicate_groups = find_duplicates()

    if not duplicate_groups:
        print("\nNo duplicates to remove!")
        return

    # Step 2: Show what would be removed
    print("\n" + "=" * 80)
    print("REMOVAL PLAN")
    print("=" * 80)
    print()
    remove_duplicates(dry_run=True)

    # Step 3: Ask for confirmation
    print("\n" + "=" * 80)
    response = input("\nDo you want to remove these duplicates? (yes/no): ").strip().lower()

    if response == 'yes':
        removed = remove_duplicates(dry_run=False)
        print("\n" + "=" * 80)
        print(f"SUCCESS! Removed {removed} duplicate entries")
        print("=" * 80)

        # Show final count
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total = cursor.fetchone()[0]
        conn.close()

        print(f"\nTotal jobs remaining in database: {total}")
    else:
        print("\nOperation cancelled. No changes made.")


if __name__ == '__main__':
    main()