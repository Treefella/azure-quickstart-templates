#!/usr/bin/env python3
"""
Gmail Job Parser - Main execution script

This tool automatically parses Gmail emails to find job opportunities using Ollama AI models.
Features:
- Detects job-related emails
- Identifies application confirmations
- Extracts structured job information
- Prevents duplicate processing
- Uses multiple Ollama models for different tasks
"""
import argparse
import logging
import sys
from job_detector import JobDetector
import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Gmail Job Parser - Automatically parse emails for job opportunities using Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process up to 50 emails
  python main.py --max-emails 50

  # Use custom search query
  python main.py --query "from:linkedin.com OR from:indeed.com"

  # List all found jobs
  python main.py --list-jobs

  # Export jobs to CSV
  python main.py --export jobs.csv

  # Process emails and show statistics only
  python main.py --max-emails 20 --stats-only

Environment Variables:
  OLLAMA_BASE_URL              Ollama server URL (default: http://localhost:11434)
  OLLAMA_JOB_DETECTION_MODEL   Model for job detection (default: llama3.2)
  OLLAMA_JOB_EXTRACTION_MODEL  Model for job extraction (default: llama3.2)
  OLLAMA_CONFIRMATION_MODEL    Model for confirmation detection (default: llama3.2)
  LOG_LEVEL                    Logging level (default: INFO)
        """
    )

    parser.add_argument(
        '--max-emails',
        type=int,
        default=100,
        help='Maximum number of emails to process (default: 100)'
    )

    parser.add_argument(
        '--query',
        type=str,
        help='Custom Gmail search query (default: config.GMAIL_QUERY)'
    )

    parser.add_argument(
        '--list-jobs',
        action='store_true',
        help='List all jobs found in database'
    )

    parser.add_argument(
        '--export',
        type=str,
        metavar='FILENAME',
        help='Export jobs to CSV file'
    )

    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show statistics only, skip detailed processing'
    )

    parser.add_argument(
        '--update-status',
        nargs=2,
        metavar=('EMAIL_ID', 'STATUS'),
        help='Update job status by email ID'
    )

    parser.add_argument(
        '--clear-old',
        type=int,
        metavar='DAYS',
        help='Clear processed emails older than DAYS'
    )

    args = parser.parse_args()

    try:
        # Initialize job detector
        logger.info("Initializing Gmail Job Parser...")
        detector = JobDetector()

        # Handle different operations
        if args.list_jobs:
            detector.print_jobs_summary()
            return 0

        if args.export:
            detector.export_jobs_to_csv(args.export)
            return 0

        if args.update_status:
            email_id, status = args.update_status
            detector.update_job_status(email_id, status)
            return 0

        if args.clear_old:
            detector.duplicate_tracker.clear_old_entries(args.clear_old)
            return 0

        if args.stats_only:
            stats = detector.duplicate_tracker.get_statistics()
            print("\n" + "="*60)
            print("STATISTICS")
            print("="*60)
            print(f"Total emails processed: {stats['total_processed']}")
            print(f"Job-related emails: {stats['job_emails']}")
            print(f"Application confirmations: {stats['confirmation_emails']}")
            print(f"Jobs in database: {len(detector.jobs_database)}")
            print("="*60 + "\n")
            return 0

        # Process emails
        detector.process_emails(max_emails=args.max_emails, query=args.query)

        # Show jobs summary
        detector.print_jobs_summary()

        logger.info("Processing complete!")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("\nSetup instructions:")
        logger.error("1. Download Gmail API credentials from Google Cloud Console")
        logger.error("2. Save as 'credentials.json' in the gmail-job-parser directory")
        logger.error("3. Ensure Ollama is running: ollama serve")
        logger.error("4. Pull required models: ollama pull llama3.2")
        return 1

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        return 130

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
