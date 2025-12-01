"""
Comprehensive database audit to find any remaining duplicates
"""

import sqlite3

def audit_database():
    """Audit database for duplicates using all fields"""
    conn = sqlite3.connect('jobs.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("DATABASE AUDIT - COMPREHENSIVE DUPLICATE CHECK")
    print("=" * 80)
    print()

    # Check 1: Exact duplicates (all fields match)
    print("CHECK 1: Exact duplicates (all 7 fields match)")
    print("-" * 80)
    cursor.execute('''
        SELECT
            title, company, location, salary, date_listed, job_type,
            SUBSTR(description, 1, 100) as desc_snippet,
            COUNT(*) as count,
            GROUP_CONCAT(id) as ids,
            GROUP_CONCAT(url, ' || ') as urls
        FROM jobs
        WHERE title IS NOT NULL AND company IS NOT NULL
        GROUP BY title, company, location, salary, date_listed, job_type, description
        HAVING count > 1
        ORDER BY count DESC
    ''')

    exact_dupes = cursor.fetchall()

    if exact_dupes:
        print(f"Found {len(exact_dupes)} groups of exact duplicates")
        print()
        for i, row in enumerate(exact_dupes, 1):
            print(f"Group {i}: {row['count']} identical entries")
            print(f"  Title: {row['title']}")
            print(f"  Company: {row['company']}")
            print(f"  Location: {row['location']}")
            print(f"  Salary: {row['salary']}")
            print(f"  Date: {row['date_listed']}")
            print(f"  Type: {row['job_type']}")
            print(f"  IDs: {row['ids']}")
            print()
    else:
        print("OK - No exact duplicates found!")
        print()

    # Check 2: Same job (title, company, location, description) - our main check
    print()
    print("CHECK 2: Same job content (title + company + location + description)")
    print("-" * 80)
    cursor.execute('''
        SELECT
            title, company, location,
            SUBSTR(description, 1, 100) as desc_snippet,
            COUNT(*) as count,
            GROUP_CONCAT(id) as ids
        FROM jobs
        WHERE title IS NOT NULL AND company IS NOT NULL
        GROUP BY title, company, location, SUBSTR(description, 1, 200)
        HAVING count > 1
        ORDER BY count DESC
    ''')

    content_dupes = cursor.fetchall()

    if content_dupes:
        print(f"Found {len(content_dupes)} groups with same content (different URLs allowed)")
        total_dupes = sum(row['count'] - 1 for row in content_dupes)
        print(f"Total duplicate entries: {total_dupes}")
        print()

        if len(content_dupes) <= 10:
            for i, row in enumerate(content_dupes, 1):
                print(f"Group {i}: {row['count']} entries")
                print(f"  Title: {row['title']}")
                print(f"  Company: {row['company']}")
                print(f"  Location: {row['location']}")
                print(f"  IDs: {row['ids']}")
                print()
        else:
            print(f"Showing first 10 of {len(content_dupes)} groups:")
            for i, row in enumerate(content_dupes[:10], 1):
                print(f"Group {i}: {row['count']} entries - {row['title']} @ {row['company']}")
            print(f"... and {len(content_dupes) - 10} more groups")
            print()
    else:
        print("OK - No content duplicates found!")
        print()

    # Check 3: Same title + company + location (different descriptions)
    print()
    print("CHECK 3: Same job identity (title + company + location) but different descriptions")
    print("-" * 80)
    cursor.execute('''
        SELECT
            title, company, location,
            COUNT(DISTINCT SUBSTR(description, 1, 200)) as desc_variations,
            COUNT(*) as total_count,
            GROUP_CONCAT(id) as ids
        FROM jobs
        WHERE title IS NOT NULL AND company IS NOT NULL
        GROUP BY title, company, location
        HAVING total_count > 1 AND desc_variations > 1
        ORDER BY total_count DESC
        LIMIT 20
    ''')

    identity_dupes = cursor.fetchall()

    if identity_dupes:
        print(f"Found {len(identity_dupes)} jobs with same title/company/location but different descriptions")
        print("(These might be legitimate - same position reposted with updated descriptions)")
        print()
        for i, row in enumerate(identity_dupes[:10], 1):
            print(f"{i}. {row['title']} @ {row['company']} - {row['location']}")
            print(f"   {row['total_count']} entries with {row['desc_variations']} different descriptions")
            print(f"   IDs: {row['ids']}")
            print()
    else:
        print("OK - No jobs with same identity but different descriptions")
        print()

    # Check 4: URL duplicates
    print()
    print("CHECK 4: Duplicate URLs")
    print("-" * 80)
    cursor.execute('''
        SELECT url, COUNT(*) as count, GROUP_CONCAT(id) as ids
        FROM jobs
        GROUP BY url
        HAVING count > 1
    ''')

    url_dupes = cursor.fetchall()

    if url_dupes:
        print(f"Found {len(url_dupes)} duplicate URLs")
        for row in url_dupes[:10]:
            print(f"  URL appears {row['count']} times: {row['url'][:80]}...")
            print(f"  IDs: {row['ids']}")
            print()
    else:
        print("OK - No duplicate URLs!")
        print()

    # Summary
    print()
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)

    cursor.execute('SELECT COUNT(*) FROM jobs')
    total_jobs = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT url) FROM jobs')
    unique_urls = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) FROM (
            SELECT title, company, location, SUBSTR(description, 1, 200)
            FROM jobs
            WHERE title IS NOT NULL AND company IS NOT NULL
            GROUP BY title, company, location, SUBSTR(description, 1, 200)
        )
    ''')
    unique_content = cursor.fetchone()[0]

    print(f"Total jobs in database: {total_jobs}")
    print(f"Unique URLs: {unique_urls}")
    print(f"Unique content (title+company+location+desc): {unique_content}")
    print()

    if unique_urls == total_jobs:
        print("OK - All URLs are unique")
    else:
        print(f"WARNING - {total_jobs - unique_urls} duplicate URLs exist")

    if unique_content == total_jobs:
        print("OK - All job content is unique")
    else:
        print(f"INFO - {total_jobs - unique_content} jobs have duplicate content (different URLs)")

    print()
    conn.close()


if __name__ == '__main__':
    audit_database()