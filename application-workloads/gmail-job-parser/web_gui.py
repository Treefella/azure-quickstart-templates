#!/usr/bin/env python3
"""
Gmail Job Parser - Web GUI
Modern web interface that runs in your browser
"""
from flask import Flask, render_template, jsonify, request, send_file
import json
import os
from pathlib import Path
from datetime import datetime
import threading
import webbrowser

# Import our modules
import config
from job_detector import JobDetector
from cv_profile import CVProfile

app = Flask(__name__)

# Global state
detector = None
profile = None
jobs_data = []
stats = {}

def load_data():
    """Load jobs and profile"""
    global detector, profile, jobs_data, stats

    # Load CV profile
    profile_path = Path('profiles/graeme_suddick_profile.json')
    if profile_path.exists():
        profile = CVProfile(str(profile_path))
    else:
        profile = CVProfile()

    # Load detector
    detector = JobDetector()

    # Load jobs
    if config.JOBS_DATABASE_FILE.exists():
        with open(config.JOBS_DATABASE_FILE, 'r') as f:
            jobs_data = json.load(f)

        # Score and categorize
        score_jobs()

    update_stats()

def score_jobs():
    """Score all jobs based on CV profile"""
    global jobs_data, profile

    for job in jobs_data:
        relevance = profile.calculate_job_relevance(job)
        job['relevance_score'] = relevance['score']
        job['matched_skills'] = relevance['matched_skills']
        job['matched_technologies'] = relevance['matched_technologies']
        job['matched_roles'] = relevance['matched_roles']
        job['total_matches'] = relevance['total_matches']

        # Categorize priority
        job['priority'] = categorize_priority(job, relevance)

def categorize_priority(job, relevance):
    """Determine job priority"""
    score = relevance['score']
    location = str(job.get('location', '')).lower()

    # Check location preference
    ne_locations = ['remote', 'durham', 'newcastle', 'north east', 'northeast',
                   'sunderland', 'consett', 'gateshead', 'hybrid']
    location_match = any(loc in location for loc in ne_locations)

    if score >= 70:
        return "high" if location_match else "medium"
    elif score >= 50:
        return "medium" if location_match else "low"
    elif score >= 30:
        return "low"
    else:
        return "check"

def update_stats():
    """Update statistics"""
    global jobs_data, stats

    stats = {
        'total': len(jobs_data),
        'high': len([j for j in jobs_data if j.get('priority') == 'high']),
        'medium': len([j for j in jobs_data if j.get('priority') == 'medium']),
        'low': len([j for j in jobs_data if j.get('priority') == 'low']),
        'check': len([j for j in jobs_data if j.get('priority') == 'check'])
    }

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/jobs')
def get_jobs():
    """Get all jobs"""
    return jsonify({
        'jobs': jobs_data,
        'stats': stats
    })

@app.route('/api/jobs/<job_id>')
def get_job(job_id):
    """Get specific job details"""
    job = next((j for j in jobs_data if j.get('email_id') == job_id), None)
    if job:
        return jsonify(job)
    return jsonify({'error': 'Job not found'}), 404

@app.route('/api/filter', methods=['POST'])
def filter_jobs():
    """Filter jobs based on criteria"""
    filters = request.json

    filtered = jobs_data.copy()

    # Priority filter
    if filters.get('priority') and filters['priority'] != 'all':
        filtered = [j for j in filtered if j.get('priority') == filters['priority']]

    # Location filter
    if filters.get('location') and filters['location'] != 'all':
        loc_filter = filters['location'].lower()
        if loc_filter == 'remote':
            filtered = [j for j in filtered if 'remote' in str(j.get('location', '')).lower()]
        elif loc_filter == 'north-east':
            ne_locs = ['durham', 'newcastle', 'sunderland', 'north east', 'northeast']
            filtered = [j for j in filtered if any(loc in str(j.get('location', '')).lower() for loc in ne_locs)]
        elif loc_filter == 'hybrid':
            filtered = [j for j in filtered if 'hybrid' in str(j.get('location', '')).lower()]

    # Search filter
    if filters.get('search'):
        search = filters['search'].lower()
        filtered = [j for j in filtered if
                   search in str(j.get('position', '')).lower() or
                   search in str(j.get('company', '')).lower() or
                   search in str(j.get('description', '')).lower()]

    # Sort by priority and score
    priority_order = {'high': 0, 'medium': 1, 'low': 2, 'check': 3}
    filtered.sort(key=lambda x: (priority_order.get(x.get('priority', 'check'), 3),
                                 -x.get('relevance_score', 0)))

    return jsonify({
        'jobs': filtered,
        'count': len(filtered)
    })

@app.route('/api/fetch', methods=['POST'])
def fetch_jobs():
    """Fetch new jobs from Gmail"""
    try:
        max_emails = request.json.get('max_emails', 50)

        # Run in thread to avoid blocking
        def fetch_thread():
            global jobs_data
            detector.process_emails(max_emails=max_emails)
            load_data()

        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()

        return jsonify({'status': 'started', 'message': f'Fetching {max_emails} emails...'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_jobs():
    """Export jobs to CSV"""
    try:
        filters = request.json

        # Apply filters
        filtered = jobs_data.copy()

        if filters.get('priority') and filters['priority'] != 'all':
            filtered = [j for j in filtered if j.get('priority') == filters['priority']]

        # Create CSV
        import csv
        filename = f"jobs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = config.DATA_DIR / filename

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['priority', 'score', 'position', 'company', 'location',
                         'job_type', 'salary', 'matched_skills', 'email_subject']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for job in filtered:
                row = job.copy()
                row['score'] = job.get('relevance_score', 0)
                row['matched_skills'] = ', '.join(job.get('matched_skills', [])[:5])
                writer.writerow(row)

        return jsonify({
            'status': 'success',
            'filename': filename,
            'count': len(filtered)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get statistics"""
    return jsonify(stats)

@app.route('/api/profile')
def get_profile():
    """Get CV profile info"""
    if profile:
        return jsonify({
            'name': profile.profile_data.get('name', 'Unknown'),
            'description': profile.profile_data.get('description', ''),
            'skills_count': len(profile.skills),
            'technologies_count': len(profile.technologies),
            'roles_count': len(profile.preferred_roles),
            'top_skills': list(profile.skills)[:10],
            'top_technologies': list(profile.technologies)[:10]
        })
    return jsonify({'error': 'Profile not loaded'}), 404

def open_browser():
    """Open browser after short delay"""
    import time
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print("="*60)
    print("Gmail Job Parser - Web GUI")
    print("="*60)
    print("\nLoading data...")

    # Load data
    load_data()

    print(f"Loaded {len(jobs_data)} jobs")
    print(f"Profile: {profile.profile_data.get('name', 'Unknown') if profile else 'Not loaded'}")
    print("\nStarting web server...")
    print("Opening browser at http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    print("="*60)

    # Open browser
    threading.Thread(target=open_browser, daemon=True).start()

    # Run Flask
    app.run(debug=False, host='0.0.0.0', port=5000)
