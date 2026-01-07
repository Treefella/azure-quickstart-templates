#!/usr/bin/env python3
"""
Search for EUC (End User Computing) jobs

This script demonstrates:
1. Using CV profile for keyword-based job searching
2. Scoring jobs based on relevance to EUC skills
3. Filtering and ranking jobs by match score
"""
import sys
import logging
from cv_profile import create_euc_profile
from job_detector import JobDetector
import config

logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Search for EUC jobs and rank by relevance"""

    print("="*80)
    print("EUC Job Search - End User Computing Specialist")
    print("="*80)
    print()

    # Create EUC profile
    logger.info("Creating EUC specialist profile...")
    euc_profile = create_euc_profile()

    print("CV Profile Summary:")
    print(euc_profile)
    print()

    # Generate Gmail query based on profile
    query = euc_profile.get_gmail_query()
    print(f"Generated Gmail Query:")
    print(f"  {query}")
    print()

    # Initialize job detector
    logger.info("Initializing job detector...")
    detector = JobDetector()

    # Process emails with EUC-focused query
    print("Searching for EUC jobs...")
    print("-" * 80)

    detector.process_emails(
        max_emails=100,
        query=query
    )

    # Get all jobs from database
    all_jobs = detector.get_jobs()

    if not all_jobs:
        print("\nNo jobs found. Try processing more emails or adjusting the query.")
        return 0

    # Score each job based on CV profile
    print(f"\nScoring {len(all_jobs)} jobs based on EUC profile...")
    print("="*80)

    scored_jobs = []
    for job in all_jobs:
        relevance = euc_profile.calculate_job_relevance(job)
        job['relevance_score'] = relevance['score']
        job['relevance_details'] = relevance
        scored_jobs.append(job)

    # Sort by relevance score (highest first)
    scored_jobs.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Display results
    print("\nTop EUC Job Matches:")
    print("="*80)

    for i, job in enumerate(scored_jobs[:20], 1):  # Top 20
        score = job['relevance_score']
        details = job['relevance_details']

        # Determine match quality
        if score >= 70:
            quality = "🔥 EXCELLENT MATCH"
        elif score >= 50:
            quality = "✓ GOOD MATCH"
        elif score >= 30:
            quality = "○ MODERATE MATCH"
        else:
            quality = "- LOW MATCH"

        print(f"\n{i}. {quality} - Score: {score:.1f}%")
        print(f"   Position: {job.get('position', 'Unknown')}")
        print(f"   Company: {job.get('company', 'Unknown')}")

        if job.get('location'):
            print(f"   Location: {job.get('location')}")

        if job.get('salary'):
            print(f"   Salary: {job.get('salary')}")

        # Show matched keywords
        if details['matched_roles']:
            print(f"   ✓ Matched Roles: {', '.join(details['matched_roles'][:3])}")

        if details['matched_technologies']:
            print(f"   ✓ Matched Tech: {', '.join(details['matched_technologies'][:5])}")

        if details['matched_skills']:
            print(f"   ✓ Matched Skills: {', '.join(details['matched_skills'][:5])}")

        print(f"   Total Matches: {details['total_matches']}")
        print(f"   Email: {job.get('email_subject', '')[:60]}...")

    # Statistics
    print("\n" + "="*80)
    print("SEARCH STATISTICS")
    print("="*80)

    excellent_matches = len([j for j in scored_jobs if j['relevance_score'] >= 70])
    good_matches = len([j for j in scored_jobs if 50 <= j['relevance_score'] < 70])
    moderate_matches = len([j for j in scored_jobs if 30 <= j['relevance_score'] < 50])
    low_matches = len([j for j in scored_jobs if j['relevance_score'] < 30])

    print(f"Total jobs analyzed: {len(scored_jobs)}")
    print(f"  🔥 Excellent matches (70%+): {excellent_matches}")
    print(f"  ✓ Good matches (50-69%): {good_matches}")
    print(f"  ○ Moderate matches (30-49%): {moderate_matches}")
    print(f"  - Low matches (<30%): {low_matches}")
    print()

    # Top matched technologies
    all_tech_matches = {}
    for job in scored_jobs:
        for tech in job['relevance_details']['matched_technologies']:
            all_tech_matches[tech] = all_tech_matches.get(tech, 0) + 1

    if all_tech_matches:
        print("Most Requested EUC Technologies:")
        sorted_tech = sorted(all_tech_matches.items(), key=lambda x: x[1], reverse=True)
        for tech, count in sorted_tech[:10]:
            print(f"  • {tech}: {count} jobs")
        print()

    # Export excellent matches
    excellent_jobs = [j for j in scored_jobs if j['relevance_score'] >= 70]
    if excellent_jobs:
        import csv
        from datetime import datetime

        filename = f"euc_excellent_matches_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = config.DATA_DIR / filename

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['score', 'position', 'company', 'location', 'salary',
                         'matched_technologies', 'email_subject', 'email_sender']

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for job in excellent_jobs:
                row = {
                    'score': job['relevance_score'],
                    'position': job.get('position', ''),
                    'company': job.get('company', ''),
                    'location': job.get('location', ''),
                    'salary': job.get('salary', ''),
                    'matched_technologies': ', '.join(job['relevance_details']['matched_technologies']),
                    'email_subject': job.get('email_subject', ''),
                    'email_sender': job.get('email_sender', '')
                }
                writer.writerow(row)

        print(f"Exported {len(excellent_jobs)} excellent matches to: {filepath}")
        print()

    print("="*80)
    print("Search complete! Focus on excellent and good matches for best results.")
    print("="*80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
