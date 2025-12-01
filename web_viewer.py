"""
Simple Flask web server to view jobs database
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB_PATH = 'jobs.db'


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Serve the HTML page"""
    return send_from_directory('.', 'jobs_viewer.html')


@app.route('/api/jobs')
def get_jobs():
    """Get jobs with optional filters"""
    search = request.args.get('search', '')
    location = request.args.get('location', '')
    company = request.args.get('company', '')
    job_type = request.args.get('job_type', '')
    triage = request.args.get('triage', 'untagged')  # Default to untagged
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query
    query = 'SELECT * FROM jobs WHERE 1=1'
    params = []

    # Triage filter
    if triage == 'untagged':
        query += ' AND (triage_status IS NULL OR triage_status = "")'
    elif triage == 'yes':
        query += ' AND triage_status = "yes"'
    elif triage == 'gsv':
        query += ' AND triage_status = "gsv"'
    elif triage == 'no':
        query += ' AND triage_status = "no"'
    # 'all' shows everything

    if search:
        query += ' AND (title LIKE ? OR company LIKE ? OR description LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])

    if location:
        query += ' AND location LIKE ?'
        params.append(f'%{location}%')

    if company:
        query += ' AND company LIKE ?'
        params.append(f'%{company}%')

    if job_type:
        query += ' AND job_type LIKE ?'
        params.append(f'%{job_type}%')

    # Count total matching results
    count_query = query.replace('SELECT *', 'SELECT COUNT(*)')
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]

    # Get paginated results
    query += ' ORDER BY first_seen DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    cursor.execute(query, params)
    jobs = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'jobs': jobs,
        'total': total,
        'limit': limit,
        'offset': offset
    })


@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    conn = get_db_connection()
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

    # Unique companies
    cursor.execute('SELECT COUNT(DISTINCT company) FROM jobs WHERE company IS NOT NULL')
    stats['unique_companies'] = cursor.fetchone()[0]

    # Unique locations
    cursor.execute('SELECT COUNT(DISTINCT location) FROM jobs WHERE location IS NOT NULL')
    stats['unique_locations'] = cursor.fetchone()[0]

    # Top companies
    cursor.execute('''
        SELECT company, COUNT(*) as count
        FROM jobs
        WHERE company IS NOT NULL AND company != ''
        GROUP BY company
        ORDER BY count DESC
        LIMIT 10
    ''')
    stats['top_companies'] = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]

    # Top locations
    cursor.execute('''
        SELECT location, COUNT(*) as count
        FROM jobs
        WHERE location IS NOT NULL AND location != ''
        GROUP BY location
        ORDER BY count DESC
        LIMIT 10
    ''')
    stats['top_locations'] = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]

    # Job types distribution
    cursor.execute('''
        SELECT job_type, COUNT(*) as count
        FROM jobs
        WHERE job_type IS NOT NULL AND job_type != ''
        GROUP BY job_type
        ORDER BY count DESC
    ''')
    stats['job_types'] = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]

    conn.close()

    return jsonify(stats)


@app.route('/api/locations')
def get_locations():
    """Get unique locations for dropdown"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT location
        FROM jobs
        WHERE location IS NOT NULL AND location != ''
        ORDER BY location
    ''')

    locations = [row[0] for row in cursor.fetchall()]
    conn.close()

    return jsonify(locations)


@app.route('/api/companies')
def get_companies():
    """Get unique companies for dropdown"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT company
        FROM jobs
        WHERE company IS NOT NULL AND company != ''
        ORDER BY company
    ''')

    companies = [row[0] for row in cursor.fetchall()]
    conn.close()

    return jsonify(companies)


@app.route('/api/triage/<int:job_id>', methods=['POST'])
def update_triage(job_id):
    """Update triage status for a job"""
    data = request.json
    status = data.get('status')  # 'yes', 'gsv', or 'no'

    if status not in ['yes', 'gsv', 'no']:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE jobs SET triage_status = ? WHERE id = ?', (status, job_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'job_id': job_id, 'status': status})


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print("=" * 60)
    print("Seek Jobs Viewer")
    print("=" * 60)
    print("\nStarting web server...")
    print(f"\nOn this computer: http://localhost:5500")
    print(f"On your iPhone:   http://{local_ip}:5500")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5500)