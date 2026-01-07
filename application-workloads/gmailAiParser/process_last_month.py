#!/usr/bin/env python3
"""
Process last month of emails and evaluate against CV profile
"""
import sys
import io
import logging
from datetime import datetime, timedelta
from job_detector import JobDetector
from cv_profile import CVProfile
import json
import config

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Process last month of emails and score against CV"""

    print("=" * 60)
    print("Gmail Job Parser - Last Month Analysis")
    print("=" * 60)
    print()

    # Calculate date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Gmail date format: YYYY/MM/DD
    date_query = f"after:{start_date.strftime('%Y/%m/%d')}"

    # Add job-related keywords to the query
    full_query = f"{date_query} (job OR hiring OR position OR opportunity OR career OR recruitment)"

    print(f"📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"🔍 Query: {full_query}")
    print()

    # Load CV profile
    profile_path = 'profiles/graeme_suddick_profile.json'
    print(f"📋 Loading CV Profile: {profile_path}")
    cv_profile = CVProfile(profile_path)
    print(f"   ✓ Skills: {len(cv_profile.profile['skills'])}")
    print(f"   ✓ Technologies: {len(cv_profile.profile['technologies'])}")
    print(f"   ✓ Preferred roles: {len(cv_profile.profile['preferred_roles'])}")
    print()

    # Initialize job detector
    print("🤖 Initializing Ollama with phi3:mini model...")
    print(f"   Ollama URL: {config.OLLAMA_BASE_URL}")
    detector = JobDetector()
    print("   ✓ Connected to Ollama")
    print()

    # Fetch and process emails
    print("📧 Fetching emails from Gmail...")
    try:
        detector.process_emails(max_emails=200, query=full_query)
    except Exception as e:
        logger.error(f"Error processing emails: {e}")
        print(f"❌ Error: {e}")
        return

    print()
    print("=" * 60)
    print("Scoring Jobs Against Your CV")
    print("=" * 60)
    print()

    # Load processed jobs
    jobs_file = config.JOBS_DATABASE_FILE
    if not jobs_file.exists():
        print("❌ No jobs found. The jobs database is empty.")
        return

    with open(jobs_file, 'r') as f:
        all_jobs = json.load(f)

    # Score each job
    scored_jobs = []
    for job in all_jobs:
        relevance = cv_profile.calculate_job_relevance(job)
        job['relevance_score'] = relevance['score']
        job['matched_skills'] = relevance['matched_skills']
        job['matched_technologies'] = relevance['matched_technologies']
        job['matched_roles'] = relevance['matched_roles']
        job['location_match'] = relevance['location_match']
        scored_jobs.append(job)

    # Sort by relevance score
    scored_jobs.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Categorize by priority
    high_priority = [j for j in scored_jobs if j['relevance_score'] >= 70 and j.get('location_match')]
    medium_priority = [j for j in scored_jobs if 50 <= j['relevance_score'] < 70]
    low_priority = [j for j in scored_jobs if 30 <= j['relevance_score'] < 50]
    check_priority = [j for j in scored_jobs if j['relevance_score'] < 30]

    # Display summary
    print(f"📊 Total Jobs Found: {len(scored_jobs)}")
    print()
    print(f"🔴 High Priority: {len(high_priority)} jobs (70%+ match + preferred location)")
    print(f"🟠 Medium Priority: {len(medium_priority)} jobs (50-69% match)")
    print(f"🟡 Low Priority: {len(low_priority)} jobs (30-49% match)")
    print(f"⚪ Check: {len(check_priority)} jobs (<30% match)")
    print()

    # Display top 10 jobs
    print("=" * 60)
    print("Top 10 Jobs by Relevance")
    print("=" * 60)
    print()

    for i, job in enumerate(scored_jobs[:10], 1):
        priority = "🔴 HIGH" if job in high_priority else "🟠 MEDIUM" if job in medium_priority else "🟡 LOW" if job in low_priority else "⚪ CHECK"

        print(f"{i}. [{priority}] {job.get('position', 'Unknown Position')} - {job['relevance_score']:.0f}% match")
        print(f"   Company: {job.get('company', 'Unknown')}")
        print(f"   Location: {job.get('location', 'Not specified')}")

        if job.get('matched_skills'):
            print(f"   Matched Skills: {', '.join(job['matched_skills'][:5])}")
        if job.get('matched_technologies'):
            print(f"   Matched Technologies: {', '.join(job['matched_technologies'][:5])}")
        if job.get('matched_roles'):
            print(f"   Matched Roles: {', '.join(job['matched_roles'][:3])}")

        print()

    # Save scored results
    output_file = config.DATA_DIR / "scored_jobs_last_month.json"
    with open(output_file, 'w') as f:
        json.dump(scored_jobs, f, indent=2)

    print(f"💾 Full results saved to: {output_file}")
    print()

    # Export high priority jobs to CSV
    if high_priority:
        import csv
        csv_file = config.DATA_DIR / "high_priority_jobs.csv"

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'position', 'company', 'location', 'relevance_score',
                'matched_skills', 'matched_technologies', 'matched_roles',
                'email_subject', 'email_date'
            ])
            writer.writeheader()

            for job in high_priority:
                writer.writerow({
                    'position': job.get('position', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'relevance_score': f"{job['relevance_score']:.0f}%",
                    'matched_skills': ', '.join(job.get('matched_skills', [])),
                    'matched_technologies': ', '.join(job.get('matched_technologies', [])),
                    'matched_roles': ', '.join(job.get('matched_roles', [])),
                    'email_subject': job.get('subject', ''),
                    'email_date': job.get('date', '')
                })

        print(f"📊 High priority jobs exported to: {csv_file}")
        print()

    print("=" * 60)
    print("✅ Analysis Complete!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Review high priority jobs in the web GUI: py web_gui.py")
    print(f"2. Check the CSV export: {config.DATA_DIR / 'high_priority_jobs.csv'}")
    print("3. Update your CV profile if needed to improve matching")
    print()

if __name__ == "__main__":
    main()
