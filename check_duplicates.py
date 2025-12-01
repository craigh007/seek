"""Check for duplicate entries in the jobs database"""
import sqlite3

conn = sqlite3.connect('jobs.db')
cursor = conn.cursor()

# Check for duplicate URLs
cursor.execute('SELECT url, COUNT(*) as count FROM jobs GROUP BY url HAVING count > 1')
dupes = cursor.fetchall()

print("=" * 60)
print("DUPLICATE CHECK REPORT")
print("=" * 60)

print(f"\nURLs appearing multiple times: {len(dupes)}")

if dupes:
    print("\nDuplicate URLs found:")
    for url, count in dupes[:20]:
        print(f"  {count} times: {url}")

        # Get the details of these duplicates
        cursor.execute('SELECT id, title, company, location FROM jobs WHERE url = ?', (url,))
        jobs = cursor.fetchall()
        for job_id, title, company, location in jobs:
            print(f"    ID {job_id}: {title} @ {company} - {location}")
        print()
else:
    print("OK - No duplicate URLs found!")

# Check for same title + company + location (different URLs)
print("\n" + "=" * 60)
print("CHECKING FOR SAME JOB WITH DIFFERENT URLS")
print("=" * 60)

cursor.execute('''
    SELECT title, company, location, COUNT(*) as count, GROUP_CONCAT(url, ' | ') as urls
    FROM jobs
    WHERE title IS NOT NULL AND company IS NOT NULL
    GROUP BY title, company, location
    HAVING count > 1
    ORDER BY count DESC
    LIMIT 20
''')

similar_jobs = cursor.fetchall()

if similar_jobs:
    print(f"\nFound {len(similar_jobs)} jobs with same title/company/location but different URLs:")
    for title, company, location, count, urls in similar_jobs:
        print(f"\n  {count} times: {title}")
        print(f"    Company: {company}")
        print(f"    Location: {location}")
        print(f"    URLs: {urls[:100]}...")
else:
    print("\nOK - No similar jobs with different URLs found!")

# Database constraints check
print("\n" + "=" * 60)
print("DATABASE SCHEMA CHECK")
print("=" * 60)

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='jobs'")
schema = cursor.fetchone()[0]
print(schema)

if 'UNIQUE' in schema and 'url' in schema:
    print("\nOK - URL column has UNIQUE constraint")
else:
    print("\nWARNING: URL column does NOT have UNIQUE constraint!")

conn.close()