"""
Configuration settings for Gmail Job Parser
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Data storage
DATA_DIR = BASE_DIR / "data"
PROCESSED_EMAILS_FILE = DATA_DIR / "processed_emails.json"
JOBS_DATABASE_FILE = DATA_DIR / "jobs.json"

# Gmail API settings
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
GMAIL_TOKEN_FILE = DATA_DIR / "token.json"
GMAIL_CREDENTIALS_FILE = BASE_DIR / "credentials.json"

# Query parameters
GMAIL_MAX_RESULTS = 100  # Number of emails to fetch per batch
GMAIL_QUERY = "subject:(job OR hiring OR position OR opportunity OR application OR career)"

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Multiple models for different tasks
OLLAMA_MODELS = {
    "job_detection": os.getenv("OLLAMA_JOB_DETECTION_MODEL", "llama3.2"),
    "job_extraction": os.getenv("OLLAMA_JOB_EXTRACTION_MODEL", "llama3.2"),
    "confirmation_detection": os.getenv("OLLAMA_CONFIRMATION_MODEL", "llama3.2")
}

# Job keywords for initial filtering
JOB_KEYWORDS = [
    "job", "position", "opportunity", "hiring", "career",
    "employment", "role", "vacancy", "opening", "application",
    "recruiter", "recruitment", "talent", "candidate"
]

# Job application confirmation keywords
CONFIRMATION_KEYWORDS = [
    "application received", "thank you for applying", "received your application",
    "application submitted", "confirm your application", "application confirmation",
    "successfully applied", "application status", "we received your",
    "thank you for your interest"
]

# Duplicate detection settings
SIMILARITY_THRESHOLD = 0.85  # Threshold for considering emails as duplicates

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
