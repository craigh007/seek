"""
Remove duplicate jobs - simplified version without unicode issues
"""

import sqlite3

def remove_duplicates():
    """Remove duplicate entries, keeping the oldest one"""
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()

    print("=" * 80)
    print("REMOVING DUPLICATES")
    print("=" * 80)
    print()

    # Get count before
    cursor.execute('SELECT COUNT(*) FROM jobs')
    before_count = cursor.fetchone()[0]
    print(f"Jobs before cleanup: {before_count}")

    # Find duplicates and their IDs ordered by first_seen
    cursor.execute('''
        SELECT
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

    print(f"Found {len(duplicate_groups)} duplicate groups")
    print()

    for row in duplicate_groups:
        ids = [int(x) for x in row[0].split(',')]
        keep_id = ids[0]  # Keep the first one (oldest by first_seen)
        remove_ids = ids[1:]  # Remove the rest

        for remove_id in remove_ids:
            cursor.execute('DELETE FROM jobs WHERE id = ?', (remove_id,))
            total_removed += 1

        if total_removed % 50 == 0:
            print(f"Removed {total_removed} duplicates so far...")

    conn.commit()

    # Get count after
    cursor.execute('SELECT COUNT(*) FROM jobs')
    after_count = cursor.fetchone()[0]

    print()
    print("=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)
    print(f"Jobs before:  {before_count}")
    print(f"Jobs removed: {total_removed}")
    print(f"Jobs after:   {after_count}")
    print()

    conn.close()
    return total_removed


if __name__ == '__main__':
    remove_duplicates()
