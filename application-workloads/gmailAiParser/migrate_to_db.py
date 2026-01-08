#!/usr/bin/env python3
"""
Migrate existing JSON data to PostgreSQL database
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from db_client import get_db_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_date(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return None
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        try:
            # Try other common formats
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None


def migrate_jobs(db_client):
    """Migrate jobs from JSON to database"""
    jobs_file = Path('data/jobs_database.json')

    if not jobs_file.exists():
        logger.warning(f"Jobs file not found: {jobs_file}")
        return 0

    logger.info(f"Reading jobs from {jobs_file}")

    try:
        with open(jobs_file, 'r') as f:
            jobs = json.load(f)

        logger.info(f"Found {len(jobs)} jobs to migrate")

        migrated = 0
        for job in jobs:
            # Parse dates
            if 'email_date' in job and isinstance(job['email_date'], str):
                job['email_date'] = parse_date(job['email_date'])

            if 'found_at' in job and isinstance(job['found_at'], str):
                job['found_at'] = parse_date(job['found_at'])

            if 'application_deadline' in job and isinstance(job['application_deadline'], str):
                job['application_deadline'] = parse_date(job['application_deadline'])

            # Add to database
            result = db_client.add_job(job)
            if result:
                migrated += 1

        logger.info(f"Successfully migrated {migrated}/{len(jobs)} jobs")
        return migrated

    except Exception as e:
        logger.error(f"Failed to migrate jobs: {e}")
        return 0


def migrate_processed_emails(db_client):
    """Migrate processed emails from JSON to database"""
    processed_file = Path('data/processed_emails.json')

    if not processed_file.exists():
        logger.warning(f"Processed emails file not found: {processed_file}")
        return 0

    logger.info(f"Reading processed emails from {processed_file}")

    try:
        with open(processed_file, 'r') as f:
            data = json.load(f)

        # Old format has 'processed_emails' key
        if isinstance(data, dict):
            emails = data.get('processed_emails', [])
        else:
            emails = data

        logger.info(f"Found {len(emails)} processed emails to migrate")

        migrated = 0
        for email in emails:
            # Parse date
            if 'date' in email and isinstance(email['date'], str):
                email['date'] = parse_date(email['date'])

            # Extract email_id if it's in the email dict
            if 'email' in email and 'id' in email['email']:
                email['email_id'] = email['email']['id']
                email['subject'] = email['email'].get('subject', '')
                email['sender'] = email['email'].get('sender', '')
                email['date'] = parse_date(email['email'].get('date', ''))
                email['snippet'] = email['email'].get('snippet', '')

            # Add to database
            result = db_client.add_processed_email(email)
            if result:
                migrated += 1

        logger.info(f"Successfully migrated {migrated}/{len(emails)} processed emails")
        return migrated

    except Exception as e:
        logger.error(f"Failed to migrate processed emails: {e}")
        return 0


def main():
    """Main migration function"""
    print("=" * 60)
    print("Gmail Job Parser - Database Migration")
    print("=" * 60)
    print()

    # Initialize database client
    logger.info("Connecting to database...")
    db_client = get_db_client()

    # Migrate jobs
    print("\n📦 Migrating jobs...")
    jobs_count = migrate_jobs(db_client)

    # Migrate processed emails
    print("\n📧 Migrating processed emails...")
    emails_count = migrate_processed_emails(db_client)

    # Show statistics
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print("=" * 60)
    print(f"✅ Jobs migrated: {jobs_count}")
    print(f"✅ Emails migrated: {emails_count}")
    print()

    # Show database stats
    stats = db_client.get_stats()
    print("📊 Database Statistics:")
    print(f"  Total jobs: {stats.get('total_jobs', 0)}")
    print(f"  Total processed emails: {stats.get('total_processed_emails', 0)}")
    print(f"  Job emails: {stats.get('job_emails', 0)}")
    print(f"  High priority jobs: {stats.get('high_priority_jobs', 0)}")
    print()
    print("=" * 60)


if __name__ == '__main__':
    main()
