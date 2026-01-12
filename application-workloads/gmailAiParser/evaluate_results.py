#!/usr/bin/env python3
"""
Multi-functional team evaluation of job parsing results
Validates AI accuracy, data quality, and CV matching correctness
"""
import sys
import io
import json
import random
from pathlib import Path
from datetime import datetime
from cv_profile import CVProfile

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class DataQualityAnalyst:
    """Validates data extraction quality and completeness"""

    def __init__(self, jobs_data):
        self.jobs = jobs_data

    def evaluate(self):
        """Evaluate data quality"""
        print("=" * 60)
        print("📊 DATA QUALITY ANALYST - Field Completeness Report")
        print("=" * 60)
        print()

        total = len(self.jobs)

        # Check field completeness
        fields = {
            'position': 0,
            'company': 0,
            'location': 0,
            'salary': 0,
            'requirements': 0,
            'description': 0,
            'email_id': 0
        }

        for job in self.jobs:
            for field in fields:
                if job.get(field) and str(job.get(field)).strip() and job.get(field) != 'Unknown':
                    fields[field] += 1

        print(f"Total Jobs Analyzed: {total}\n")
        print("Field Completeness:")
        print("-" * 60)

        for field, count in sorted(fields.items(), key=lambda x: -x[1]):
            percentage = (count / total * 100) if total > 0 else 0
            bar = "█" * int(percentage / 2) + "░" * (50 - int(percentage / 2))
            status = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"{status} {field:15s} {bar} {percentage:5.1f}% ({count}/{total})")

        print()

        # Data quality score
        avg_completeness = sum(fields.values()) / len(fields) / total * 100 if total > 0 else 0

        if avg_completeness >= 80:
            grade = "A - Excellent"
            emoji = "🌟"
        elif avg_completeness >= 70:
            grade = "B - Good"
            emoji = "✅"
        elif avg_completeness >= 60:
            grade = "C - Acceptable"
            emoji = "⚠️"
        else:
            grade = "D - Needs Improvement"
            emoji = "❌"

        print(f"{emoji} Overall Data Quality: {avg_completeness:.1f}% - Grade: {grade}")
        print()

        return {
            'completeness': fields,
            'average': avg_completeness,
            'grade': grade
        }

class AIAccuracyValidator:
    """Validates AI job detection and extraction accuracy"""

    def __init__(self, jobs_data):
        self.jobs = jobs_data

    def evaluate(self, sample_size=10):
        """Manual validation of random sample"""
        print("=" * 60)
        print("🤖 AI ACCURACY VALIDATOR - Manual Review")
        print("=" * 60)
        print()

        sample = random.sample(self.jobs, min(sample_size, len(self.jobs)))

        print(f"Reviewing {len(sample)} random jobs for validation...")
        print("For each job, verify if the AI extracted information correctly.")
        print()

        correct = 0
        total = len(sample)

        for i, job in enumerate(sample, 1):
            print(f"\n{'='*60}")
            print(f"Job {i}/{total}")
            print(f"{'='*60}")
            print(f"Position: {job.get('position', 'N/A')}")
            print(f"Company: {job.get('company', 'N/A')}")
            print(f"Location: {job.get('location', 'N/A')}")
            print(f"Email Subject: {job.get('subject', 'N/A')}")
            print()
            print(f"Description Preview:")
            desc = job.get('description', '')
            print(f"  {desc[:200]}..." if len(desc) > 200 else f"  {desc}")
            print()

            # Ask for validation
            while True:
                response = input("Is this extraction CORRECT? (y/n/s=skip): ").lower().strip()
                if response in ['y', 'n', 's']:
                    break
                print("Please enter 'y' for yes, 'n' for no, or 's' to skip")

            if response == 'y':
                correct += 1
            elif response == 's':
                total -= 1

        if total > 0:
            accuracy = (correct / total * 100)

            print()
            print("=" * 60)
            print("AI Accuracy Results")
            print("=" * 60)
            print(f"Correct: {correct}/{total}")
            print(f"Accuracy: {accuracy:.1f}%")

            if accuracy >= 90:
                print("🌟 Grade: A - Excellent AI Performance")
            elif accuracy >= 80:
                print("✅ Grade: B - Good AI Performance")
            elif accuracy >= 70:
                print("⚠️  Grade: C - Acceptable, Consider Tuning")
            else:
                print("❌ Grade: D - Needs Improvement")
            print()

            return {'accuracy': accuracy, 'correct': correct, 'total': total}
        else:
            print("\nNo jobs validated.")
            return None

class CVMatchingValidator:
    """Validates CV-based relevance scoring accuracy"""

    def __init__(self, jobs_data, cv_profile):
        self.jobs = jobs_data
        self.cv_profile = cv_profile

    def evaluate(self):
        """Evaluate CV matching accuracy"""
        print("=" * 60)
        print("🎯 CV MATCHING VALIDATOR - Relevance Score Analysis")
        print("=" * 60)
        print()

        # Score all jobs
        scored_jobs = []
        for job in self.jobs:
            relevance = self.cv_profile.calculate_job_relevance(job)
            job['relevance_score'] = relevance['score']
            job['matched_skills'] = relevance['matched_skills']
            job['matched_technologies'] = relevance['matched_technologies']
            job['location_match'] = relevance['location_match']
            scored_jobs.append(job)

        # Categorize by priority
        high = [j for j in scored_jobs if j['relevance_score'] >= 70 and j.get('location_match')]
        medium = [j for j in scored_jobs if 50 <= j['relevance_score'] < 70]
        low = [j for j in scored_jobs if 30 <= j['relevance_score'] < 50]
        check = [j for j in scored_jobs if j['relevance_score'] < 30]

        print("Priority Distribution:")
        print("-" * 60)
        print(f"🔴 High Priority:   {len(high):3d} jobs ({len(high)/len(scored_jobs)*100:5.1f}%)")
        print(f"🟠 Medium Priority: {len(medium):3d} jobs ({len(medium)/len(scored_jobs)*100:5.1f}%)")
        print(f"🟡 Low Priority:    {len(low):3d} jobs ({len(low)/len(scored_jobs)*100:5.1f}%)")
        print(f"⚪ Check Priority:  {len(check):3d} jobs ({len(check)/len(scored_jobs)*100:5.1f}%)")
        print()

        # Show top matches
        top_jobs = sorted(scored_jobs, key=lambda x: x['relevance_score'], reverse=True)[:5]

        print("Top 5 Matches (for manual verification):")
        print("-" * 60)
        for i, job in enumerate(top_jobs, 1):
            print(f"{i}. {job.get('position', 'Unknown')} @ {job.get('company', 'Unknown')}")
            print(f"   Score: {job['relevance_score']:.0f}% | Location: {job.get('location', 'N/A')}")
            if job.get('matched_skills'):
                print(f"   Skills: {', '.join(job['matched_skills'][:5])}")
            print()

        # Check for potential false positives in high priority
        print("\n⚠️  Manual Review Recommended For:")
        print("-" * 60)

        suspicious = [j for j in high if j['relevance_score'] >= 90]
        if suspicious:
            print(f"🔍 {len(suspicious)} jobs with >90% match (verify these aren't false positives)")
            for job in suspicious[:3]:
                print(f"   - {job.get('position')} @ {job.get('company')}")

        low_skills = [j for j in high if len(j.get('matched_skills', [])) < 3]
        if low_skills:
            print(f"🔍 {len(low_skills)} high-priority jobs with <3 matched skills (verify relevance)")
            for job in low_skills[:3]:
                print(f"   - {job.get('position')} @ {job.get('company')} ({len(job.get('matched_skills', []))} skills)")

        print()

        return {
            'distribution': {'high': len(high), 'medium': len(medium), 'low': len(low), 'check': len(check)},
            'top_matches': top_jobs[:5],
            'suspicious_high': len(suspicious),
            'low_skill_matches': len(low_skills)
        }

class FalsePositiveDetector:
    """Detects potential false positives in job detection"""

    def __init__(self, jobs_data):
        self.jobs = jobs_data

    def evaluate(self):
        """Detect potential false positives"""
        print("=" * 60)
        print("🚨 FALSE POSITIVE DETECTOR - Quality Control")
        print("=" * 60)
        print()

        issues = []

        # Check for missing critical fields
        for job in self.jobs:
            if not job.get('position') or job.get('position') == 'Unknown':
                issues.append(('Missing Position', job))

            if not job.get('company') or job.get('company') == 'Unknown':
                issues.append(('Missing Company', job))

            # Check for suspiciously short descriptions
            desc = job.get('description', '')
            if len(desc) < 50:
                issues.append(('Short Description', job))

        print(f"Potential Issues Found: {len(issues)}")
        print("-" * 60)

        issue_types = {}
        for issue_type, job in issues:
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

        for issue_type, count in sorted(issue_types.items(), key=lambda x: -x[1]):
            print(f"  {issue_type}: {count} jobs")

        print()

        if issues:
            print("Sample Issues (first 5):")
            for issue_type, job in issues[:5]:
                print(f"  [{issue_type}] {job.get('position', 'Unknown')} @ {job.get('company', 'Unknown')}")
                print(f"    Subject: {job.get('subject', 'N/A')[:60]}")

        print()

        false_positive_rate = len(issues) / len(self.jobs) * 100 if self.jobs else 0

        if false_positive_rate < 5:
            print(f"✅ False Positive Rate: {false_positive_rate:.1f}% - Excellent")
        elif false_positive_rate < 10:
            print(f"⚠️  False Positive Rate: {false_positive_rate:.1f}% - Acceptable")
        else:
            print(f"❌ False Positive Rate: {false_positive_rate:.1f}% - Needs Improvement")

        print()

        return {
            'total_issues': len(issues),
            'issue_types': issue_types,
            'false_positive_rate': false_positive_rate
        }

def main():
    """Run comprehensive evaluation"""
    print("\n")
    print("🔬" * 30)
    print("GMAIL JOB PARSER - COMPREHENSIVE EVALUATION")
    print("Multi-Functional Team Analysis")
    print("🔬" * 30)
    print("\n")

    # Load data
    jobs_file = Path('data/jobs.json')

    if not jobs_file.exists():
        print("❌ Error: No jobs data found at data/jobs.json")
        print("   Run 'py process_last_month.py' first to generate data.")
        return

    with open(jobs_file, 'r') as f:
        jobs = json.load(f)

    print(f"📊 Loaded {len(jobs)} jobs for evaluation\n")

    # Load CV profile
    cv_profile = CVProfile('profiles/graeme_suddick_profile.json')

    # Run evaluations
    results = {}

    # 1. Data Quality Analysis
    dqa = DataQualityAnalyst(jobs)
    results['data_quality'] = dqa.evaluate()

    # 2. CV Matching Validation
    cvv = CVMatchingValidator(jobs, cv_profile)
    results['cv_matching'] = cvv.evaluate()

    # 3. False Positive Detection
    fpd = FalsePositiveDetector(jobs)
    results['false_positives'] = fpd.evaluate()

    # 4. AI Accuracy (manual validation)
    print("=" * 60)
    print("🤖 AI ACCURACY VALIDATION")
    print("=" * 60)
    print()
    print("Would you like to manually validate AI accuracy?")
    print("This will show you 10 random jobs for you to verify.")
    response = input("Validate AI accuracy? (y/n): ").lower().strip()

    if response == 'y':
        aiv = AIAccuracyValidator(jobs)
        results['ai_accuracy'] = aiv.evaluate(sample_size=10)

    # Final Summary
    print("\n")
    print("=" * 60)
    print("📋 FINAL EVALUATION SUMMARY")
    print("=" * 60)
    print()

    print(f"Data Quality Score: {results['data_quality']['average']:.1f}% - {results['data_quality']['grade']}")
    print(f"High Priority Jobs: {results['cv_matching']['distribution']['high']}")
    print(f"False Positive Rate: {results['false_positives']['false_positive_rate']:.1f}%")

    if results.get('ai_accuracy'):
        print(f"AI Accuracy: {results['ai_accuracy']['accuracy']:.1f}%")

    print()

    # Overall grade
    scores = [results['data_quality']['average']]
    if results.get('ai_accuracy'):
        scores.append(results['ai_accuracy']['accuracy'])

    overall = sum(scores) / len(scores)

    if overall >= 85:
        print("🌟 Overall System Performance: EXCELLENT")
        print("   The AI is performing well. Results are highly reliable.")
    elif overall >= 75:
        print("✅ Overall System Performance: GOOD")
        print("   The AI is performing adequately. Minor improvements possible.")
    elif overall >= 65:
        print("⚠️  Overall System Performance: ACCEPTABLE")
        print("   Consider reviewing and tuning the AI model.")
    else:
        print("❌ Overall System Performance: NEEDS IMPROVEMENT")
        print("   Significant tuning required. Review prompts and model selection.")

    print()

    # Save results
    report_file = Path('data/evaluation_report.json')
    results['timestamp'] = datetime.now().isoformat()
    results['overall_score'] = overall

    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"💾 Full report saved to: {report_file}")
    print()

if __name__ == "__main__":
    main()
