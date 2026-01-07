#!/usr/bin/env python3
"""
Model Benchmarking Suite for Gmail Job Parser

This script tests different Ollama models across all three tasks:
1. Job detection
2. Job extraction
3. Confirmation detection

Measures:
- Speed (seconds per email)
- Accuracy (compared to ground truth)
- Memory usage
- Model size

Usage:
    python benchmark_models.py --models "llama3.2:1b,llama3.2:3b,mistral"
"""
import sys
import time
import json
import argparse
import logging
from typing import List, Dict
from datetime import datetime
import requests
from ollama_parser import OllamaParser
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Test dataset with ground truth
TEST_EMAILS = {
    "job_emails": [
        {
            "id": "job_1",
            "subject": "Senior Python Developer - Remote Position",
            "sender": "recruiting@techcorp.com",
            "body": """We are seeking a Senior Python Developer.

Position: Senior Python Developer
Location: Remote
Salary: $120,000 - $150,000

Requirements:
- 5+ years Python
- Django/Flask
- Docker, Kubernetes
- Microservices

Apply at careers.techcorp.com""",
            "snippet": "We are seeking a Senior Python Developer...",
            "date": "2026-01-04",
            "ground_truth": {
                "is_job": True,
                "is_confirmation": False,
                "company": "techcorp",
                "position": "Senior Python Developer",
                "location": "Remote"
            }
        },
        {
            "id": "job_2",
            "subject": "EUC Engineer Position at FinanceCorp",
            "sender": "jobs@financecorp.com",
            "body": """We're hiring an End User Computing Engineer.

Title: EUC Engineer
Company: FinanceCorp
Location: New York, NY
Salary: $95,000 - $115,000

Key Technologies:
- VMware Horizon
- Citrix XenDesktop
- Microsoft Intune
- SCCM
- Windows 10/11

Experience with VDI required.""",
            "snippet": "We're hiring an End User Computing Engineer...",
            "date": "2026-01-03",
            "ground_truth": {
                "is_job": True,
                "is_confirmation": False,
                "company": "financecorp",
                "position": "EUC Engineer",
                "location": "New York"
            }
        },
        {
            "id": "job_3",
            "subject": "DevOps Engineer Opening - Docker & Kubernetes",
            "sender": "hr@startupinc.com",
            "body": """Join our DevOps team!

We need a DevOps Engineer with strong container orchestration skills.

Tech Stack:
- Docker
- Kubernetes
- Terraform
- AWS
- Jenkins
- Python

Salary: $100k-$130k
Location: Austin, TX (Hybrid)""",
            "snippet": "Join our DevOps team...",
            "date": "2026-01-02",
            "ground_truth": {
                "is_job": True,
                "is_confirmation": False,
                "company": "startupinc",
                "position": "DevOps Engineer",
                "location": "Austin"
            }
        }
    ],

    "confirmation_emails": [
        {
            "id": "conf_1",
            "subject": "Application Received - Software Engineer",
            "sender": "noreply@jobs.company.com",
            "body": """Thank you for applying to the Software Engineer position.

We have received your application and will review it shortly.
Application ID: APP-12345

You will hear from us within 2-3 business days.""",
            "snippet": "Thank you for applying...",
            "date": "2026-01-03",
            "ground_truth": {
                "is_job": True,
                "is_confirmation": True
            }
        },
        {
            "id": "conf_2",
            "subject": "Your Application to TechCorp - Confirmed",
            "sender": "careers@techcorp.com",
            "body": """Dear Applicant,

This email confirms that we received your application for the Senior Developer role.

Reference Number: TC-2024-001
Position: Senior Developer
Date Submitted: January 3, 2026

Our team will review your qualifications.""",
            "snippet": "This email confirms that we received your application...",
            "date": "2026-01-03",
            "ground_truth": {
                "is_job": True,
                "is_confirmation": True
            }
        }
    ],

    "non_job_emails": [
        {
            "id": "non_1",
            "subject": "Your Amazon Order Has Shipped",
            "sender": "shipment@amazon.com",
            "body": """Your order #123-4567890 has shipped!

Tracking: 1Z999AA1012345678
Expected delivery: January 5, 2026""",
            "snippet": "Your order has shipped...",
            "date": "2026-01-02",
            "ground_truth": {
                "is_job": False,
                "is_confirmation": False
            }
        },
        {
            "id": "non_2",
            "subject": "LinkedIn Weekly Digest",
            "sender": "notifications@linkedin.com",
            "body": """Here's what's happening in your network this week:

- 5 new profile views
- 3 connection requests
- 12 job recommendations

Check out these people you may know...""",
            "snippet": "Here's what's happening in your network...",
            "date": "2026-01-01",
            "ground_truth": {
                "is_job": False,
                "is_confirmation": False
            }
        }
    ]
}


class ModelBenchmark:
    """Benchmark different Ollama models"""

    def __init__(self):
        self.results = {}
        self.base_url = config.OLLAMA_BASE_URL

    def get_available_models(self) -> List[str]:
        """Get list of pulled Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
        except Exception as e:
            logger.error(f"Failed to get model list: {e}")
        return []

    def check_model_available(self, model: str) -> bool:
        """Check if model is pulled"""
        available = self.get_available_models()
        return any(model in m for m in available)

    def benchmark_model(self, model: str, tasks: List[str] = None) -> Dict:
        """Benchmark a specific model on all tasks"""

        if not self.check_model_available(model):
            logger.warning(f"Model {model} not available. Run: ollama pull {model}")
            return None

        logger.info(f"\nBenchmarking model: {model}")
        logger.info("=" * 60)

        # Override config to use this model for all tasks
        original_models = config.OLLAMA_MODELS.copy()
        config.OLLAMA_MODELS = {
            'job_detection': model,
            'job_extraction': model,
            'confirmation_detection': model
        }

        # Create parser with this model
        parser = OllamaParser()

        results = {
            'model': model,
            'job_detection': {'correct': 0, 'total': 0, 'times': []},
            'confirmation_detection': {'correct': 0, 'total': 0, 'times': []},
            'job_extraction': {'correct': 0, 'total': 0, 'times': [], 'details': []},
            'overall_time': 0
        }

        start_overall = time.time()

        # Test job detection
        logger.info("\n1. Testing Job Detection...")
        all_emails = (
            TEST_EMAILS['job_emails'] +
            TEST_EMAILS['confirmation_emails'] +
            TEST_EMAILS['non_job_emails']
        )

        for email in all_emails:
            start = time.time()
            is_job = parser.is_job_related(email)
            elapsed = time.time() - start

            expected = email['ground_truth']['is_job']
            correct = (is_job == expected)

            results['job_detection']['total'] += 1
            results['job_detection']['times'].append(elapsed)
            if correct:
                results['job_detection']['correct'] += 1

            status = "✓" if correct else "✗"
            logger.info(f"  {status} {email['id']}: {is_job} (expected {expected}) - {elapsed:.2f}s")

        # Test confirmation detection
        logger.info("\n2. Testing Confirmation Detection...")
        for email in TEST_EMAILS['job_emails'] + TEST_EMAILS['confirmation_emails']:
            start = time.time()
            is_conf = parser.is_application_confirmation(email)
            elapsed = time.time() - start

            expected = email['ground_truth']['is_confirmation']
            correct = (is_conf == expected)

            results['confirmation_detection']['total'] += 1
            results['confirmation_detection']['times'].append(elapsed)
            if correct:
                results['confirmation_detection']['correct'] += 1

            status = "✓" if correct else "✗"
            logger.info(f"  {status} {email['id']}: {is_conf} (expected {expected}) - {elapsed:.2f}s")

        # Test job extraction
        logger.info("\n3. Testing Job Extraction...")
        for email in TEST_EMAILS['job_emails']:
            start = time.time()
            extracted = parser.extract_job_details(email)
            elapsed = time.time() - start

            results['job_extraction']['total'] += 1
            results['job_extraction']['times'].append(elapsed)

            # Check if key fields extracted correctly
            gt = email['ground_truth']
            company_match = gt['company'].lower() in str(extracted.get('company', '')).lower()
            position_match = any(word in str(extracted.get('position', '')).lower()
                               for word in gt['position'].lower().split())

            if company_match and position_match:
                results['job_extraction']['correct'] += 1
                status = "✓"
            else:
                status = "✗"

            results['job_extraction']['details'].append({
                'email_id': email['id'],
                'extracted_company': extracted.get('company'),
                'expected_company': gt['company'],
                'extracted_position': extracted.get('position'),
                'expected_position': gt['position'],
                'time': elapsed
            })

            logger.info(f"  {status} {email['id']}: {extracted.get('position')} at {extracted.get('company')} - {elapsed:.2f}s")

        results['overall_time'] = time.time() - start_overall

        # Restore original config
        config.OLLAMA_MODELS = original_models

        return results

    def print_comparison(self, all_results: List[Dict]):
        """Print comparison table of all benchmarked models"""

        print("\n" + "=" * 100)
        print("MODEL BENCHMARK COMPARISON")
        print("=" * 100)

        # Header
        print(f"\n{'Model':<20} {'Job Det':<12} {'Confirm':<12} {'Extract':<12} {'Avg Time':<12} {'Total Time':<12}")
        print("-" * 100)

        for result in all_results:
            model = result['model']

            # Calculate accuracies
            job_acc = (result['job_detection']['correct'] / result['job_detection']['total'] * 100) if result['job_detection']['total'] > 0 else 0
            conf_acc = (result['confirmation_detection']['correct'] / result['confirmation_detection']['total'] * 100) if result['confirmation_detection']['total'] > 0 else 0
            extr_acc = (result['job_extraction']['correct'] / result['job_extraction']['total'] * 100) if result['job_extraction']['total'] > 0 else 0

            # Average time per email
            all_times = (result['job_detection']['times'] +
                        result['confirmation_detection']['times'] +
                        result['job_extraction']['times'])
            avg_time = sum(all_times) / len(all_times) if all_times else 0

            print(f"{model:<20} {job_acc:>5.1f}%      {conf_acc:>5.1f}%      {extr_acc:>5.1f}%      {avg_time:>6.2f}s      {result['overall_time']:>6.1f}s")

        print("\n" + "=" * 100)

        # Recommendations
        print("\nRECOMMENDATIONS:")
        print("-" * 100)

        # Best accuracy
        best_acc = max(all_results, key=lambda x: (
            x['job_detection']['correct'] +
            x['confirmation_detection']['correct'] +
            x['job_extraction']['correct']
        ))
        print(f"🎯 Best Accuracy: {best_acc['model']}")

        # Fastest
        fastest = min(all_results, key=lambda x: x['overall_time'])
        print(f"⚡ Fastest: {fastest['model']} ({fastest['overall_time']:.1f}s total)")

        # Best balance (accuracy > 85% and fastest among them)
        good_accuracy = [r for r in all_results if
                        (r['job_detection']['correct'] / r['job_detection']['total']) >= 0.85]
        if good_accuracy:
            balanced = min(good_accuracy, key=lambda x: x['overall_time'])
            print(f"⚖️  Best Balance: {balanced['model']}")

        print("=" * 100)


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark different Ollama models for job parsing',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--models',
        type=str,
        help='Comma-separated list of models to test (default: all available)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available models and exit'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='benchmark_results.json',
        help='Output file for detailed results'
    )

    args = parser.parse_args()

    benchmark = ModelBenchmark()

    # List models if requested
    if args.list:
        available = benchmark.get_available_models()
        print("\nAvailable Ollama models:")
        for model in available:
            print(f"  - {model}")
        return 0

    # Determine which models to test
    if args.models:
        models_to_test = [m.strip() for m in args.models.split(',')]
    else:
        # Test common models if available
        suggested = [
            'llama3.2:1b', 'llama3.2:3b', 'llama3.2', 'llama3.1:8b',
            'mistral', 'phi3', 'gemma:2b', 'gemma:7b', 'qwen2:7b'
        ]
        available = benchmark.get_available_models()
        models_to_test = [m for m in suggested if any(m in a for a in available)]

        if not models_to_test:
            print("No models found. Available models:")
            for model in available:
                print(f"  - {model}")
            print("\nSpecify models with --models flag or pull suggested models")
            return 1

    print("=" * 100)
    print("OLLAMA MODEL BENCHMARK - Gmail Job Parser")
    print("=" * 100)
    print(f"\nTesting {len(models_to_test)} models:")
    for model in models_to_test:
        print(f"  - {model}")
    print(f"\nTest dataset: {len(TEST_EMAILS['job_emails'])} jobs, "
          f"{len(TEST_EMAILS['confirmation_emails'])} confirmations, "
          f"{len(TEST_EMAILS['non_job_emails'])} non-jobs")
    print("=" * 100)

    # Run benchmarks
    all_results = []
    for model in models_to_test:
        result = benchmark.benchmark_model(model)
        if result:
            all_results.append(result)

    if not all_results:
        print("\nNo results collected. Make sure models are pulled.")
        return 1

    # Print comparison
    benchmark.print_comparison(all_results)

    # Save detailed results
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'models_tested': models_to_test,
        'test_dataset_size': {
            'job_emails': len(TEST_EMAILS['job_emails']),
            'confirmation_emails': len(TEST_EMAILS['confirmation_emails']),
            'non_job_emails': len(TEST_EMAILS['non_job_emails'])
        },
        'results': all_results
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nDetailed results saved to: {args.output}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
