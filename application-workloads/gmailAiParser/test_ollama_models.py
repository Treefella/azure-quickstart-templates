#!/usr/bin/env python3
"""
Test script to verify Ollama models are working correctly

This script tests:
1. Ollama connection
2. Model availability
3. Job detection capability
4. Job extraction capability
5. Confirmation detection capability
"""
import sys
import json
from ollama_parser import OllamaParser
import config

# Test email samples
TEST_EMAILS = {
    "job_posting": {
        "id": "test_job_1",
        "subject": "Senior Python Developer - Remote Position",
        "sender": "recruiting@techcorp.com",
        "date": "2026-01-04",
        "body": """
We are seeking a Senior Python Developer to join our team.

Position: Senior Python Developer
Location: Remote
Salary: $120,000 - $150,000

Requirements:
- 5+ years of Python experience
- Experience with Django/Flask
- Docker and Kubernetes knowledge
- Strong understanding of microservices architecture

Please apply at careers.techcorp.com
        """,
        "snippet": "We are seeking a Senior Python Developer to join our team..."
    },

    "application_confirmation": {
        "id": "test_conf_1",
        "subject": "Application Received - Software Engineer Position",
        "sender": "noreply@jobs.company.com",
        "date": "2026-01-03",
        "body": """
Thank you for applying to the Software Engineer position at Company Inc.

We have received your application and our team will review it shortly.
You will hear from us within 2-3 business days.

Application ID: APP-12345
Position: Software Engineer
Applied: January 3, 2026
        """,
        "snippet": "Thank you for applying to the Software Engineer position..."
    },

    "non_job": {
        "id": "test_non_1",
        "subject": "Your Amazon Order Has Shipped",
        "sender": "shipment@amazon.com",
        "date": "2026-01-02",
        "body": """
Your order #123-4567890 has shipped!

Tracking number: 1Z999AA1012345678
Expected delivery: January 5, 2026

Thank you for shopping with Amazon.
        """,
        "snippet": "Your order has shipped..."
    }
}


def test_ollama_connection(parser):
    """Test Ollama connection"""
    print("Testing Ollama connection...")
    try:
        import requests
        response = requests.get(f"{parser.base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✓ Connected to Ollama")
            print(f"  Available models: {[m['name'] for m in models]}")
            return True
        else:
            print(f"✗ Failed to connect to Ollama (status {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_job_detection(parser):
    """Test job detection capability"""
    print("\nTesting job detection...")

    # Test job posting (should be True)
    result = parser.is_job_related(TEST_EMAILS["job_posting"])
    if result:
        print("✓ Job posting correctly identified")
    else:
        print("✗ Job posting NOT identified (false negative)")
        return False

    # Test non-job email (should be False)
    result = parser.is_job_related(TEST_EMAILS["non_job"])
    if not result:
        print("✓ Non-job email correctly rejected")
    else:
        print("✗ Non-job email incorrectly identified as job (false positive)")
        return False

    return True


def test_confirmation_detection(parser):
    """Test application confirmation detection"""
    print("\nTesting confirmation detection...")

    # Test confirmation email (should be True)
    result = parser.is_application_confirmation(TEST_EMAILS["application_confirmation"])
    if result:
        print("✓ Application confirmation correctly identified")
    else:
        print("✗ Application confirmation NOT identified (false negative)")
        return False

    # Test job posting as non-confirmation (should be False)
    result = parser.is_application_confirmation(TEST_EMAILS["job_posting"])
    if not result:
        print("✓ Job posting correctly identified as not a confirmation")
    else:
        print("✗ Job posting incorrectly identified as confirmation (false positive)")
        return False

    return True


def test_job_extraction(parser):
    """Test job detail extraction"""
    print("\nTesting job detail extraction...")

    job_details = parser.extract_job_details(TEST_EMAILS["job_posting"])

    if not job_details:
        print("✗ Failed to extract job details")
        return False

    print("✓ Job details extracted:")
    print(f"  Company: {job_details.get('company', 'N/A')}")
    print(f"  Position: {job_details.get('position', 'N/A')}")
    print(f"  Location: {job_details.get('location', 'N/A')}")
    print(f"  Salary: {job_details.get('salary', 'N/A')}")

    # Check if essential fields are present
    if job_details.get('position') or job_details.get('company'):
        print("✓ Essential fields extracted")
        return True
    else:
        print("✗ Missing essential fields")
        return False


def test_email_comparison(parser):
    """Test email similarity comparison"""
    print("\nTesting email similarity comparison...")

    email1 = TEST_EMAILS["job_posting"]
    email2 = {
        "id": "test_similar",
        "subject": "Senior Python Developer Position - Remote",
        "sender": "recruiting@techcorp.com",
        "snippet": "We are seeking a Senior Python Developer..."
    }
    email3 = TEST_EMAILS["non_job"]

    # Similar emails should have high score
    similarity_high = parser.compare_emails_for_duplicates(email1, email2)
    print(f"  Similar emails score: {similarity_high:.2%}")

    # Different emails should have low score
    similarity_low = parser.compare_emails_for_duplicates(email1, email3)
    print(f"  Different emails score: {similarity_low:.2%}")

    if similarity_high > similarity_low:
        print("✓ Similarity detection working correctly")
        return True
    else:
        print("✗ Similarity detection not working properly")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("Ollama Model Testing for Gmail Job Parser")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Ollama URL: {config.OLLAMA_BASE_URL}")
    print(f"  Job Detection Model: {config.OLLAMA_MODELS['job_detection']}")
    print(f"  Job Extraction Model: {config.OLLAMA_MODELS['job_extraction']}")
    print(f"  Confirmation Model: {config.OLLAMA_MODELS['confirmation_detection']}")
    print("="*60)

    # Initialize parser
    try:
        parser = OllamaParser()
    except Exception as e:
        print(f"\n✗ Failed to initialize OllamaParser: {e}")
        print("\nMake sure Ollama is running:")
        print("  Docker: docker-compose up -d")
        print("  Local: ollama serve")
        return 1

    # Run tests
    tests = [
        ("Connection", test_ollama_connection),
        ("Job Detection", test_job_detection),
        ("Confirmation Detection", test_confirmation_detection),
        ("Job Extraction", test_job_extraction),
        ("Email Comparison", test_email_comparison),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func(parser)
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            results[name] = False

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")

    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests passed! Ollama models are working correctly.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
