#!/usr/bin/env python3
"""
Example usage of the Gmail Job Parser modules

This script demonstrates how to use the parser programmatically
for custom workflows and integrations.
"""

from gmail_client import GmailClient
from ollama_parser import OllamaParser
from job_detector import JobDetector
from duplicate_tracker import DuplicateTracker


def example_basic_usage():
    """Basic usage example - process emails and list jobs"""
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Initialize the job detector (this initializes all components)
    detector = JobDetector()

    # Process emails
    print("Processing emails...")
    detector.process_emails(max_emails=20)

    # Get all jobs
    jobs = detector.get_jobs()
    print(f"\nFound {len(jobs)} total jobs")

    # Print job summary
    detector.print_jobs_summary()


def example_custom_query():
    """Example with custom Gmail query"""
    print("\nExample 2: Custom Query")
    print("=" * 60)

    detector = JobDetector()

    # Process emails from specific sources
    custom_query = "from:linkedin.com OR from:indeed.com subject:(Python OR Software)"
    print(f"Using query: {custom_query}")

    detector.process_emails(max_emails=30, query=custom_query)


def example_filter_jobs():
    """Example filtering and working with jobs"""
    print("\nExample 3: Filter and Work with Jobs")
    print("=" * 60)

    detector = JobDetector()

    # Get all jobs
    all_jobs = detector.get_jobs()
    print(f"Total jobs: {len(all_jobs)}")

    # Filter jobs by status
    new_jobs = detector.get_jobs(status='new')
    print(f"New jobs: {len(new_jobs)}")

    # Print details of new jobs
    for job in new_jobs[:5]:  # First 5 new jobs
        print(f"\n- {job.get('position', 'Unknown')} at {job.get('company', 'Unknown')}")
        if job.get('location'):
            print(f"  Location: {job['location']}")
        if job.get('salary'):
            print(f"  Salary: {job['salary']}")


def example_manual_components():
    """Example using components manually for custom workflow"""
    print("\nExample 4: Manual Component Usage")
    print("=" * 60)

    # Initialize components separately
    gmail = GmailClient()
    ollama = OllamaParser()
    tracker = DuplicateTracker()

    # Fetch emails manually
    emails = gmail.fetch_emails(max_results=10)
    print(f"Fetched {len(emails)} emails")

    # Process each email manually
    for email in emails:
        # Skip if already processed
        if tracker.is_processed(email['id']):
            continue

        # Check if job-related
        if ollama.is_job_related(email):
            print(f"\n✓ Job found: {email['subject']}")

            # Check if it's an application confirmation
            if ollama.is_application_confirmation(email):
                print("  → This is an application confirmation")
            else:
                # Extract job details
                job_details = ollama.extract_job_details(email)
                print(f"  → Company: {job_details.get('company', 'Unknown')}")
                print(f"  → Position: {job_details.get('position', 'Unknown')}")

            # Mark as processed
            tracker.mark_as_processed(email['id'], email, is_job=True)


def example_duplicate_detection():
    """Example demonstrating duplicate detection"""
    print("\nExample 5: Duplicate Detection")
    print("=" * 60)

    tracker = DuplicateTracker()

    # Get statistics
    stats = tracker.get_statistics()
    print(f"Total processed emails: {stats['total_processed']}")
    print(f"Job emails: {stats['job_emails']}")
    print(f"Confirmations: {stats['confirmation_emails']}")

    # Example email to check for duplicates
    example_email = {
        'subject': 'Software Engineer Position at TechCorp',
        'sender': 'jobs@techcorp.com',
        'snippet': 'We are hiring for a software engineer position...'
    }

    # Find similar emails
    similar = tracker.find_similar_emails(example_email, similarity_threshold=0.7)

    if similar:
        print(f"\nFound {len(similar)} similar emails:")
        for item in similar[:3]:  # Show top 3
            email = item['email']
            score = item['similarity_score']
            print(f"  - {email['subject'][:50]}... (similarity: {score:.2f})")
    else:
        print("\nNo similar emails found")


def example_export_jobs():
    """Example exporting jobs to CSV"""
    print("\nExample 6: Export Jobs")
    print("=" * 60)

    detector = JobDetector()

    # Export all jobs
    detector.export_jobs_to_csv("example_jobs_export.csv")
    print("Jobs exported to example_jobs_export.csv")


def example_update_job_status():
    """Example updating job statuses"""
    print("\nExample 7: Update Job Status")
    print("=" * 60)

    detector = JobDetector()

    # Get first job
    jobs = detector.get_jobs()
    if jobs:
        first_job = jobs[0]
        email_id = first_job.get('email_id')

        print(f"Updating status for: {first_job.get('position', 'Unknown')}")

        # Update status
        detector.update_job_status(email_id, 'applied')
        print("Status updated to 'applied'")

        # Common statuses: 'new', 'applied', 'interview', 'offer', 'rejected'
    else:
        print("No jobs available to update")


def example_compare_emails():
    """Example using Ollama to compare emails for similarity"""
    print("\nExample 8: Compare Emails with AI")
    print("=" * 60)

    ollama = OllamaParser()

    email1 = {
        'subject': 'Senior Python Developer - Remote',
        'sender': 'recruiter@company.com',
        'snippet': 'Looking for an experienced Python developer...'
    }

    email2 = {
        'subject': 'Senior Python Developer Position',
        'sender': 'hr@company.com',
        'snippet': 'We are seeking a skilled Python developer...'
    }

    email3 = {
        'subject': 'Java Developer Needed',
        'sender': 'jobs@different.com',
        'snippet': 'Looking for Java expertise...'
    }

    # Compare emails
    similarity_1_2 = ollama.compare_emails_for_duplicates(email1, email2)
    similarity_1_3 = ollama.compare_emails_for_duplicates(email1, email3)

    print(f"Similarity between email1 and email2: {similarity_1_2:.2%}")
    print(f"Similarity between email1 and email3: {similarity_1_3:.2%}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Gmail Job Parser - Example Usage")
    print("=" * 60 + "\n")

    # Uncomment the examples you want to run:

    # example_basic_usage()
    # example_custom_query()
    # example_filter_jobs()
    # example_manual_components()
    # example_duplicate_detection()
    # example_export_jobs()
    # example_update_job_status()
    # example_compare_emails()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    main()
