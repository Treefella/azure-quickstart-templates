#!/usr/bin/env python3
"""
Real-time GUI for Gmail Job Parser
Shows live updates as emails are processed
"""
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import webbrowser
import time
from datetime import datetime, timedelta
from job_detector import JobDetector
from cv_profile import CVProfile
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gmail-job-parser-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
processing_state = {
    'is_processing': False,
    'current_email': None,
    'progress': {'current': 0, 'total': 0},
    'stats': {'new_jobs': 0, 'confirmations': 0, 'duplicates': 0, 'non_jobs': 0},
    'jobs': [],
    'status': 'Idle'
}

def emit_update():
    """Send update to all connected clients"""
    socketio.emit('update', processing_state, broadcast=True)

class RealtimeJobDetector(JobDetector):
    """Job detector with real-time GUI updates"""

    def process_emails_realtime(self, max_emails=None, query=None):
        """Process emails with real-time GUI updates"""
        global processing_state

        processing_state['is_processing'] = True
        processing_state['status'] = 'Fetching emails...'
        emit_update()

        # Fetch emails
        emails = self.gmail_client.fetch_emails(query=query, max_results=max_emails)

        if not emails:
            processing_state['is_processing'] = False
            processing_state['status'] = 'No emails to process'
            emit_update()
            return

        processing_state['progress']['total'] = len(emails)
        processing_state['status'] = f'Processing {len(emails)} emails...'
        emit_update()

        new_jobs = 0
        confirmations = 0
        duplicates = 0
        non_jobs = 0

        for i, email in enumerate(emails, 1):
            processing_state['progress']['current'] = i
            processing_state['current_email'] = {
                'subject': email['subject'],
                'sender': email['sender']
            }

            # Check if already processed
            processing_state['status'] = 'Checking for duplicates...'
            emit_update()

            if self.duplicate_tracker.is_processed(email['id']):
                duplicates += 1
                processing_state['stats'] = {
                    'new_jobs': new_jobs,
                    'confirmations': confirmations,
                    'duplicates': duplicates,
                    'non_jobs': non_jobs
                }
                processing_state['status'] = '⏭️ Already processed'
                emit_update()
                time.sleep(0.1)  # Brief pause so user can see
                continue

            # Check for similar emails
            similar_emails = self.duplicate_tracker.find_similar_emails(email)
            if similar_emails and similar_emails[0]['similarity_score'] > config.SIMILARITY_THRESHOLD:
                duplicates += 1
                processing_state['stats'] = {
                    'new_jobs': new_jobs,
                    'confirmations': confirmations,
                    'duplicates': duplicates,
                    'non_jobs': non_jobs
                }
                processing_state['status'] = f"🔄 Duplicate ({similar_emails[0]['similarity_score']:.0%})"
                emit_update()

                self.duplicate_tracker.mark_as_processed(
                    email['id'], email,
                    is_job=similar_emails[0]['email'].get('is_job', False),
                    is_confirmation=similar_emails[0]['email'].get('is_confirmation', False)
                )
                time.sleep(0.1)
                continue

            # Check if it's a confirmation
            processing_state['status'] = '🤖 Checking if confirmation...'
            emit_update()

            is_confirmation = self.ollama_parser.is_application_confirmation(email)

            if is_confirmation:
                confirmations += 1
                processing_state['stats'] = {
                    'new_jobs': new_jobs,
                    'confirmations': confirmations,
                    'duplicates': duplicates,
                    'non_jobs': non_jobs
                }
                processing_state['status'] = '✅ Application confirmation'
                emit_update()

                self.duplicate_tracker.mark_as_processed(
                    email['id'], email, is_job=True, is_confirmation=True
                )
                time.sleep(0.1)
                continue

            # Check if job-related
            processing_state['status'] = '🤖 Checking if job email...'
            emit_update()

            is_job = self.ollama_parser.is_job_related(email)

            if not is_job:
                non_jobs += 1
                processing_state['stats'] = {
                    'new_jobs': new_jobs,
                    'confirmations': confirmations,
                    'duplicates': duplicates,
                    'non_jobs': non_jobs
                }
                processing_state['status'] = '⚪ Not a job email'
                emit_update()

                self.duplicate_tracker.mark_as_processed(
                    email['id'], email, is_job=False
                )
                time.sleep(0.1)
                continue

            # Extract job details
            processing_state['status'] = '💼 Extracting job details...'
            emit_update()

            job_details = self.ollama_parser.extract_job_details(email)

            if job_details:
                job_details['found_at'] = datetime.now().isoformat()
                job_details['status'] = 'new'
                self.jobs_database.append(job_details)
                self.save_jobs_database()

                # Score the job
                cv_profile = CVProfile('profiles/graeme_suddick_profile.json')
                relevance = cv_profile.calculate_job_relevance(job_details)

                job_details['relevance_score'] = relevance['score']
                job_details['matched_skills'] = relevance['matched_skills']
                job_details['location_match'] = relevance['location_match']

                # Determine priority
                if relevance['score'] >= 70 and relevance['location_match']:
                    priority = 'High'
                    priority_class = 'high'
                elif relevance['score'] >= 50:
                    priority = 'Medium'
                    priority_class = 'medium'
                elif relevance['score'] >= 30:
                    priority = 'Low'
                    priority_class = 'low'
                else:
                    priority = 'Check'
                    priority_class = 'check'

                # Add to GUI jobs list
                processing_state['jobs'].insert(0, {
                    'position': job_details.get('position', 'Unknown'),
                    'company': job_details.get('company', 'Unknown'),
                    'location': job_details.get('location', 'Not specified'),
                    'relevance_score': int(relevance['score']),
                    'priority': priority,
                    'priority_class': priority_class,
                    'matched_skills': ', '.join(relevance['matched_skills'][:5]),
                    'email_subject': email['subject']
                })

                new_jobs += 1
                processing_state['stats'] = {
                    'new_jobs': new_jobs,
                    'confirmations': confirmations,
                    'duplicates': duplicates,
                    'non_jobs': non_jobs
                }
                processing_state['status'] = f'✅ JOB FOUND: {job_details.get("position", "Unknown")}'
                emit_update()
                time.sleep(0.5)  # Pause to let user see the new job

            # Mark as processed
            self.duplicate_tracker.mark_as_processed(
                email['id'], email, is_job=True, job_details=job_details
            )

        # Processing complete
        processing_state['is_processing'] = False
        processing_state['status'] = f'✅ Complete! Found {new_jobs} jobs'
        processing_state['current_email'] = None
        emit_update()

@app.route('/')
def index():
    """Render the real-time dashboard"""
    return render_template('realtime.html')

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    emit('update', processing_state)

@socketio.on('start_processing')
def handle_start_processing(data):
    """Start processing emails"""
    def process():
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        date_query = f"after:{start_date.strftime('%Y/%m/%d')}"
        full_query = f"{date_query} (job OR hiring OR position OR opportunity OR career OR recruitment)"

        detector = RealtimeJobDetector()
        detector.process_emails_realtime(max_emails=200, query=full_query)

    # Start processing in background thread
    thread = threading.Thread(target=process)
    thread.daemon = True
    thread.start()

    emit('processing_started', {'status': 'Processing started'})

def open_browser():
    """Open browser after short delay"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5001')

if __name__ == '__main__':
    print("=" * 60)
    print("Gmail Job Parser - Real-Time GUI")
    print("=" * 60)
    print()
    print("🌐 Starting web server...")
    print("📱 Opening browser at http://localhost:5001")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()

    # Run server
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
