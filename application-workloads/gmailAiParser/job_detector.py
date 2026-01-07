"""
Job detection and management system
"""
import json
import logging
from typing import Dict, List
from datetime import datetime
from gmail_client import GmailClient
from ollama_parser import OllamaParser
from duplicate_tracker import DuplicateTracker
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class JobDetector:
    """Main job detection and processing system"""

    def __init__(self):
        self.gmail_client = GmailClient()
        self.ollama_parser = OllamaParser()
        self.duplicate_tracker = DuplicateTracker()
        self.jobs_database_file = config.JOBS_DATABASE_FILE
        self.jobs_database: List[Dict] = []
        self.load_jobs_database()

    def load_jobs_database(self):
        """Load saved jobs from database"""
        if self.jobs_database_file.exists():
            try:
                with open(self.jobs_database_file, 'r') as f:
                    self.jobs_database = json.load(f)
                logger.info(f"Loaded {len(self.jobs_database)} jobs from database")
            except json.JSONDecodeError as e:
                logger.error(f"Error loading jobs database: {e}")
                self.jobs_database = []
        else:
            logger.info("No jobs database found, starting fresh")
            self.jobs_database = []

    def save_jobs_database(self):
        """Save jobs to database"""
        try:
            # Ensure data directory exists
            self.jobs_database_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.jobs_database_file, 'w') as f:
                json.dump(self.jobs_database, f, indent=2)
            logger.debug(f"Saved {len(self.jobs_database)} jobs to database")
        except Exception as e:
            logger.error(f"Error saving jobs database: {e}")

    def process_emails(self, max_emails: int = None, query: str = None):
        """
        Process emails from Gmail to find and extract job information

        Args:
            max_emails: Maximum number of emails to process
            query: Custom Gmail query
        """
        logger.info("Starting email processing...")

        # Fetch emails
        emails = self.gmail_client.fetch_emails(query=query, max_results=max_emails)

        if not emails:
            logger.info("No emails to process")
            return

        logger.info(f"Processing {len(emails)} emails...")

        new_jobs = 0
        confirmations = 0
        duplicates = 0
        non_jobs = 0

        for i, email in enumerate(emails, 1):
            logger.info(f"Processing email {i}/{len(emails)}: {email['subject'][:50]}...")

            # Skip if already processed
            if self.duplicate_tracker.is_processed(email['id']):
                logger.debug(f"Email {email['id']} already processed, skipping")
                duplicates += 1
                continue

            # Check for similar emails
            similar_emails = self.duplicate_tracker.find_similar_emails(email)
            if similar_emails:
                logger.info(f"Found {len(similar_emails)} similar emails")
                logger.debug(f"Most similar: {similar_emails[0]['email']['subject']} "
                           f"(score: {similar_emails[0]['similarity_score']:.2f})")

                # If very similar, mark as duplicate
                if similar_emails[0]['similarity_score'] > config.SIMILARITY_THRESHOLD:
                    logger.info("Email is a duplicate, skipping detailed processing")
                    self.duplicate_tracker.mark_as_processed(
                        email['id'],
                        email,
                        is_job=similar_emails[0]['email'].get('is_job', False),
                        is_confirmation=similar_emails[0]['email'].get('is_confirmation', False)
                    )
                    duplicates += 1
                    continue

            # Check if it's an application confirmation
            is_confirmation = self.ollama_parser.is_application_confirmation(email)

            if is_confirmation:
                logger.info("✓ Email is a job application confirmation")
                self.duplicate_tracker.mark_as_processed(
                    email['id'],
                    email,
                    is_job=True,
                    is_confirmation=True
                )
                confirmations += 1
                continue

            # Check if it's job-related
            is_job = self.ollama_parser.is_job_related(email)

            if not is_job:
                logger.debug("Email is not job-related")
                self.duplicate_tracker.mark_as_processed(
                    email['id'],
                    email,
                    is_job=False
                )
                non_jobs += 1
                continue

            # Extract job details
            logger.info("✓ Email is job-related, extracting details...")
            job_details = self.ollama_parser.extract_job_details(email)

            if job_details:
                # Add to jobs database
                job_details['found_at'] = datetime.now().isoformat()
                job_details['status'] = 'new'
                self.jobs_database.append(job_details)
                self.save_jobs_database()

                logger.info(f"✓ Extracted job: {job_details.get('position', 'Unknown')} "
                          f"at {job_details.get('company', 'Unknown')}")
                new_jobs += 1

            # Mark as processed
            self.duplicate_tracker.mark_as_processed(
                email['id'],
                email,
                is_job=True,
                job_details=job_details
            )

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("PROCESSING SUMMARY")
        logger.info("="*60)
        logger.info(f"Total emails processed: {len(emails)}")
        logger.info(f"New job opportunities found: {new_jobs}")
        logger.info(f"Application confirmations: {confirmations}")
        logger.info(f"Duplicates skipped: {duplicates}")
        logger.info(f"Non-job emails: {non_jobs}")
        logger.info("="*60)

        # Print overall statistics
        stats = self.duplicate_tracker.get_statistics()
        logger.info("\nOVERALL STATISTICS")
        logger.info("="*60)
        logger.info(f"Total emails ever processed: {stats['total_processed']}")
        logger.info(f"Total job emails: {stats['job_emails']}")
        logger.info(f"Total confirmations: {stats['confirmation_emails']}")
        logger.info(f"Total jobs in database: {len(self.jobs_database)}")
        logger.info("="*60 + "\n")

    def get_jobs(self, status: str = None) -> List[Dict]:
        """
        Get jobs from database, optionally filtered by status

        Args:
            status: Filter by status (e.g., 'new', 'applied', 'interview')

        Returns:
            List of job dictionaries
        """
        if status:
            return [job for job in self.jobs_database if job.get('status') == status]
        return self.jobs_database

    def update_job_status(self, email_id: str, status: str):
        """
        Update status of a job

        Args:
            email_id: Email ID of the job
            status: New status
        """
        for job in self.jobs_database:
            if job.get('email_id') == email_id:
                job['status'] = status
                job['updated_at'] = datetime.now().isoformat()
                self.save_jobs_database()
                logger.info(f"Updated job status to '{status}' for {job.get('position', 'Unknown')}")
                return

        logger.warning(f"Job with email_id {email_id} not found")

    def print_jobs_summary(self):
        """Print a summary of all jobs found"""
        if not self.jobs_database:
            print("\nNo jobs found yet.")
            return

        print("\n" + "="*80)
        print(f"FOUND {len(self.jobs_database)} JOB OPPORTUNITIES")
        print("="*80 + "\n")

        for i, job in enumerate(self.jobs_database, 1):
            print(f"{i}. {job.get('position', 'Unknown Position')}")
            print(f"   Company: {job.get('company', 'Unknown')}")
            if job.get('location'):
                print(f"   Location: {job.get('location')}")
            if job.get('job_type'):
                print(f"   Type: {job.get('job_type')}")
            if job.get('salary'):
                print(f"   Salary: {job.get('salary')}")
            print(f"   Status: {job.get('status', 'new')}")
            print(f"   Found: {job.get('found_at', 'Unknown')[:10]}")
            print(f"   Email: {job.get('email_subject', '')[:60]}...")
            print()

    def export_jobs_to_csv(self, filename: str = "jobs_export.csv"):
        """Export jobs to CSV file"""
        import csv

        if not self.jobs_database:
            logger.warning("No jobs to export")
            return

        fieldnames = ['position', 'company', 'location', 'job_type', 'salary',
                     'status', 'found_at', 'email_subject', 'email_sender', 'description']

        output_file = config.DATA_DIR / filename

        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.jobs_database)

            logger.info(f"Exported {len(self.jobs_database)} jobs to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
