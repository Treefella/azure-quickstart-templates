"""
Job detection and management system with live progress table
"""
import json
import logging
from typing import Dict, List
from datetime import datetime
from gmail_client import GmailClient
from ollama_parser import OllamaParser
from duplicate_tracker import DuplicateTracker
import config

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

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
        if RICH_AVAILABLE:
            return self._process_emails_with_live_table(max_emails, query)
        else:
            return self._process_emails_simple(max_emails, query)

    def _create_status_table(self, current_idx, total, current_subject, status, stats, last_job=None):
        """Create the live status table"""
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Value", style="green", width=55)

        # Progress
        progress_pct = (current_idx / total * 100) if total > 0 else 0
        progress_bar = "█" * int(progress_pct / 2) + "░" * (50 - int(progress_pct / 2))
        table.add_row("Progress", f"[{current_idx}/{total}] {progress_pct:.1f}%")
        table.add_row("", progress_bar)

        # Current email
        subject_preview = current_subject[:45] + "..." if len(current_subject) > 45 else current_subject
        table.add_row("Current Email", subject_preview)
        table.add_row("AI Status", status)

        # Last job found
        if last_job:
            table.add_row("", "")
            table.add_row("🎯 Last Job Found", f"[bold green]{last_job}[/bold green]")

        # Separator
        table.add_row("", "")

        # Statistics
        table.add_row("💼 New Jobs Found", f"[bold green]{stats['new_jobs']}[/bold green]")
        table.add_row("✅ Confirmations", f"[bold cyan]{stats['confirmations']}[/bold cyan]")
        table.add_row("🔄 Duplicates Skipped", f"[bold yellow]{stats['duplicates']}[/bold yellow]")
        table.add_row("⚪ Non-Job Emails", f"[bold white]{stats['non_jobs']}[/bold white]")

        return Panel(table, title="📧 Gmail Job Parser - Live Processing", border_style="blue")

    def _process_emails_with_live_table(self, max_emails: int = None, query: str = None):
        """Process emails with live updating table"""
        logger.info("Starting email processing...")

        # Fetch emails
        emails = self.gmail_client.fetch_emails(query=query, max_results=max_emails)

        if not emails:
            logger.info("No emails to process")
            print("ℹ️  No emails to process")
            return

        console = Console()
        logger.info(f"Processing {len(emails)} emails...")

        new_jobs = 0
        confirmations = 0
        duplicates = 0
        non_jobs = 0
        last_job_found = None

        stats = {'new_jobs': new_jobs, 'confirmations': confirmations, 'duplicates': duplicates, 'non_jobs': non_jobs}

        with Live(self._create_status_table(0, len(emails), "Starting...", "Initializing", stats),
                  console=console, refresh_per_second=4) as live:

            for i, email in enumerate(emails, 1):
                subject = email['subject']
                logger.info(f"Processing email {i}/{len(emails)}: {subject[:50]}...")

                # Update table
                live.update(self._create_status_table(i, len(emails), subject, "Checking duplicate...", stats, last_job_found))

                # Skip if already processed
                if self.duplicate_tracker.is_processed(email['id']):
                    logger.debug(f"Email {email['id']} already processed, skipping")
                    duplicates += 1
                    stats = {'new_jobs': new_jobs, 'confirmations': confirmations, 'duplicates': duplicates, 'non_jobs': non_jobs}
                    live.update(self._create_status_table(i, len(emails), subject, "✅ Already processed", stats, last_job_found))
                    continue

                # Check for similar emails
                similar_emails = self.duplicate_tracker.find_similar_emails(email)
                if similar_emails:
                    logger.info(f"Found {len(similar_emails)} similar emails")

                    if similar_emails[0]['similarity_score'] > config.SIMILARITY_THRESHOLD:
                        logger.info("Email is a duplicate, skipping detailed processing")
                        self.duplicate_tracker.mark_as_processed(
                            email['id'],
                            email,
                            is_job=similar_emails[0]['email'].get('is_job', False),
                            is_confirmation=similar_emails[0]['email'].get('is_confirmation', False)
                        )
                        duplicates += 1
                        stats = {'new_jobs': new_jobs, 'confirmations': confirmations, 'duplicates': duplicates, 'non_jobs': non_jobs}
                        live.update(self._create_status_table(i, len(emails), subject, f"🔄 Duplicate ({similar_emails[0]['similarity_score']:.0%})", stats, last_job_found))
                        continue

                # Check if it's an application confirmation
                live.update(self._create_status_table(i, len(emails), subject, "🤖 Checking confirmation...", stats, last_job_found))
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
                    stats = {'new_jobs': new_jobs, 'confirmations': confirmations, 'duplicates': duplicates, 'non_jobs': non_jobs}
                    live.update(self._create_status_table(i, len(emails), subject, "✅ Confirmation detected", stats, last_job_found))
                    continue

                # Check if it's job-related
                live.update(self._create_status_table(i, len(emails), subject, "🤖 Checking if job...", stats, last_job_found))
                is_job = self.ollama_parser.is_job_related(email)

                if not is_job:
                    logger.debug("Email is not job-related")
                    self.duplicate_tracker.mark_as_processed(
                        email['id'],
                        email,
                        is_job=False
                    )
                    non_jobs += 1
                    stats = {'new_jobs': new_jobs, 'confirmations': confirmations, 'duplicates': duplicates, 'non_jobs': non_jobs}
                    live.update(self._create_status_table(i, len(emails), subject, "⚪ Not a job", stats, last_job_found))
                    continue

                # Extract job details
                live.update(self._create_status_table(i, len(emails), subject, "💼 Extracting job details...", stats, last_job_found))
                logger.info("✓ Email is job-related, extracting details...")
                job_details = self.ollama_parser.extract_job_details(email)

                if job_details:
                    # Add to jobs database
                    job_details['found_at'] = datetime.now().isoformat()
                    job_details['status'] = 'new'
                    self.jobs_database.append(job_details)
                    self.save_jobs_database()

                    position = job_details.get('position', 'Unknown Position')
                    company = job_details.get('company', 'Unknown Company')
                    location = job_details.get('location', 'Unknown')

                    last_job_found = f"{position} @ {company}"

                    logger.info(f"✓ Extracted job: {position} at {company}")
                    new_jobs += 1
                    stats = {'new_jobs': new_jobs, 'confirmations': confirmations, 'duplicates': duplicates, 'non_jobs': non_jobs}
                    live.update(self._create_status_table(i, len(emails), subject, f"✅ JOB FOUND!", stats, last_job_found))

                # Mark as processed
                self.duplicate_tracker.mark_as_processed(
                    email['id'],
                    email,
                    is_job=True,
                    job_details=job_details
                )

        # Print final summary
        console.print("\n[bold green]✅ Processing Complete![/bold green]\n")

        summary_table = Table(show_header=True, header_style="bold cyan", box=box.DOUBLE)
        summary_table.add_column("Summary", style="cyan", width=30)
        summary_table.add_column("Count", justify="right", style="bold green", width=15)

        summary_table.add_row("Total Emails Processed", str(len(emails)))
        summary_table.add_row("💼 New Job Opportunities", f"[bold green]{new_jobs}[/bold green]")
        summary_table.add_row("✅ Application Confirmations", f"[bold cyan]{confirmations}[/bold cyan]")
        summary_table.add_row("🔄 Duplicates Skipped", f"[bold yellow]{duplicates}[/bold yellow]")
        summary_table.add_row("⚪ Non-Job Emails", f"[bold white]{non_jobs}[/bold white]")

        console.print(Panel(summary_table, title="📊 Final Summary", border_style="green"))

        # Print overall statistics
        stats_data = self.duplicate_tracker.get_statistics()
        console.print(f"\n[bold]📈 Total emails ever processed:[/bold] {stats_data['total_processed']}")
        console.print(f"[bold]💼 Total jobs in database:[/bold] {len(self.jobs_database)}\n")

    def _process_emails_simple(self, max_emails: int = None, query: str = None):
        """Process emails with simple output (fallback when rich not available)"""
        # This is the old implementation for fallback
        logger.info("Rich library not available, using simple output")
        print("⚠️  Install 'rich' library for better visualization: pip install rich")
        print()

        # ... existing simple implementation code ...
        pass

    def get_jobs(self, status: str = None) -> List[Dict]:
        """Get jobs from database, optionally filtered by status"""
        if status:
            return [job for job in self.jobs_database if job.get('status') == status]
        return self.jobs_database

    def update_job_status(self, email_id: str, status: str):
        """Update status of a job"""
        for job in self.jobs_database:
            if job.get('email_id') == email_id:
                job['status'] = status
                self.save_jobs_database()
                logger.info(f"Updated job status to '{status}' for {email_id}")
                return
        logger.warning(f"Job not found with email_id {email_id}")
