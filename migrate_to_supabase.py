"""
Migrate jobs from local SQLite database to Supabase

Run this once to transfer your existing jobs.db data.
"""

import sqlite3
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def migrate(db_path: str = "jobs.db", batch_size: int = 100):
    """Migrate all jobs from SQLite to Supabase"""

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Set SUPABASE_URL and SUPABASE_KEY in .env file")
        return

    print(f"Connecting to Supabase: {url}")
    supabase = create_client(url, key)

    print(f"Opening SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs")
    total = cursor.fetchone()[0]
    print(f"Found {total} jobs to migrate")

    cursor.execute("""
        SELECT url, title, company, location, salary,
               date_listed, job_type, description,
               first_seen, last_seen, is_active, triage_status
        FROM jobs
    """)

    migrated = 0
    skipped = 0
    errors = 0
    batch = []

    for row in cursor:
        job = {
            "url": row["url"],
            "title": row["title"],
            "company": row["company"],
            "location": row["location"],
            "salary": row["salary"],
            "date_listed": row["date_listed"],
            "job_type": row["job_type"],
            "description": row["description"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "is_active": bool(row["is_active"]) if row["is_active"] is not None else True,
            "triage_status": row["triage_status"]
        }

        batch.append(job)

        if len(batch) >= batch_size:
            try:
                result = supabase.table("jobs").upsert(
                    batch,
                    on_conflict="url"
                ).execute()
                migrated += len(result.data)
                print(f"  Migrated {migrated}/{total} jobs...")
            except Exception as e:
                errors += len(batch)
                print(f"  ERROR: {e}")

            batch = []

    if batch:
        try:
            result = supabase.table("jobs").upsert(
                batch,
                on_conflict="url"
            ).execute()
            migrated += len(result.data)
        except Exception as e:
            errors += len(batch)
            print(f"  ERROR: {e}")

    conn.close()

    print("\n" + "=" * 50)
    print("Migration complete!")
    print(f"  Migrated: {migrated}")
    print(f"  Errors: {errors}")
    print("=" * 50)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate SQLite to Supabase")
    parser.add_argument("--db", default="jobs.db", help="Path to SQLite database")
    parser.add_argument("--batch", type=int, default=100, help="Batch size")

    args = parser.parse_args()

    migrate(args.db, args.batch)
