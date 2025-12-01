"""
Backfill region column for existing jobs in Supabase
Run this once after adding the region column
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from nz_locations import get_region

load_dotenv()


def backfill_regions():
    """Update all jobs with their detected region"""

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: Set SUPABASE_URL and SUPABASE_KEY in .env file")
        return

    print(f"Connecting to Supabase...")
    client = create_client(url, key)

    # Get all jobs without a region (or all jobs to re-process)
    print("Fetching jobs...")
    result = client.table("jobs").select("id, location, region").execute()

    jobs = result.data
    print(f"Found {len(jobs)} jobs to process")

    updated = 0
    skipped = 0

    for job in jobs:
        location = job.get('location') or ''
        current_region = job.get('region')
        new_region = get_region(location)

        # Only update if region changed or was empty
        if current_region != new_region:
            try:
                client.table("jobs").update({
                    "region": new_region
                }).eq("id", job['id']).execute()
                updated += 1

                if updated % 50 == 0:
                    print(f"  Updated {updated} jobs...")

            except Exception as e:
                print(f"  Error updating job {job['id']}: {e}")
        else:
            skipped += 1

    print(f"\nBackfill complete!")
    print(f"  Updated: {updated}")
    print(f"  Skipped (already correct): {skipped}")

    # Show region distribution
    print("\nRegion distribution:")
    stats = client.table("jobs").select("region").execute()
    region_counts = {}
    for job in stats.data:
        region = job.get('region') or 'Unknown'
        region_counts[region] = region_counts.get(region, 0) + 1

    for region, count in sorted(region_counts.items(), key=lambda x: -x[1]):
        print(f"  {region}: {count}")


if __name__ == "__main__":
    backfill_regions()
