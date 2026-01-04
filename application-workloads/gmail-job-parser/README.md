# Gmail Job Parser with Ollama

An intelligent Python application that automatically parses Gmail emails to find job opportunities using multiple Ollama AI models. The system identifies job-related emails, extracts structured information, detects application confirmations, and prevents duplicate processing.

## Features

- **Automated Job Detection**: Uses AI to identify job-related emails from your Gmail
- **Multi-Model Architecture**: Leverages multiple Ollama models for different tasks:
  - Job detection model
  - Job information extraction model
  - Application confirmation detection model
- **Duplicate Prevention**: Intelligent duplicate detection to avoid processing the same job multiple times
- **Application Tracking**: Identifies and tracks job application confirmation emails
- **Structured Data Extraction**: Extracts company name, position, location, salary, requirements, and more
- **Persistent Storage**: Maintains a database of processed emails and found jobs
- **Export Capabilities**: Export jobs to CSV for further analysis
- **Configurable**: Environment-based configuration for models and settings

## Prerequisites

1. **Python 3.8+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai)
3. **Gmail API Credentials** - From Google Cloud Console
4. **Ollama Models** - Default uses `llama3.2`, but you can configure other models

## Installation

### 1. Install Ollama and Pull Models

```bash
# Install Ollama (see https://ollama.ai for your OS)
# For Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# In another terminal, pull the required model
ollama pull llama3.2

# Optional: Pull other models you want to use
ollama pull mistral
ollama pull llama3.1
```

### 2. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API for your project
4. Create OAuth 2.0 credentials (Desktop application)
5. Download credentials and save as `credentials.json` in this directory

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Environment Variables

You can configure the parser using environment variables:

```bash
# Ollama server URL
export OLLAMA_BASE_URL="http://localhost:11434"

# Model for detecting job-related emails
export OLLAMA_JOB_DETECTION_MODEL="llama3.2"

# Model for extracting job information
export OLLAMA_JOB_EXTRACTION_MODEL="llama3.2"

# Model for detecting application confirmations
export OLLAMA_CONFIRMATION_MODEL="llama3.2"

# Logging level
export LOG_LEVEL="INFO"
```

### Using Different Models

You can use different Ollama models for different tasks:

```bash
# Use different models for different tasks
export OLLAMA_JOB_DETECTION_MODEL="mistral"
export OLLAMA_JOB_EXTRACTION_MODEL="llama3.1"
export OLLAMA_CONFIRMATION_MODEL="llama3.2"
```

### Configuration File

Edit `config.py` to customize:
- Gmail query parameters
- Similarity thresholds
- Job and confirmation keywords
- File paths

## Usage

### Basic Usage

```bash
# Process up to 100 emails (default)
python main.py

# Process specific number of emails
python main.py --max-emails 50

# Use custom Gmail search query
python main.py --query "from:linkedin.com OR from:indeed.com"

# Process emails from specific companies
python main.py --query "from:company.com job"
```

### View and Manage Jobs

```bash
# List all found jobs
python main.py --list-jobs

# Show statistics only
python main.py --stats-only

# Export jobs to CSV
python main.py --export my_jobs.csv
```

### Maintenance

```bash
# Clear processed emails older than 90 days
python main.py --clear-old 90

# Update job status
python main.py --update-status <EMAIL_ID> "applied"
```

## How It Works

### 1. Email Fetching
- Connects to Gmail API using OAuth2
- Fetches emails matching the configured query
- Extracts subject, sender, date, and body content

### 2. Duplicate Detection
- Checks if email was previously processed
- Compares with similar emails using AI similarity scoring
- Skips duplicates to avoid redundant processing

### 3. Job Detection
- Uses Ollama model to determine if email is job-related
- Falls back to keyword matching if AI unavailable
- Filters out non-job emails early

### 4. Application Confirmation Detection
- Identifies emails confirming job applications
- Uses specialized model for confirmation detection
- Tracks confirmations separately from job opportunities

### 5. Job Information Extraction
- Uses Ollama model to extract structured data:
  - Company name
  - Job position/title
  - Location
  - Job type (Full-time, Contract, etc.)
  - Salary information
  - Key requirements
  - Description
  - Application deadline
- Handles missing information gracefully

### 6. Data Storage
- Saves processed email IDs to prevent duplicates
- Stores extracted job information in JSON database
- Maintains metadata (found date, status, etc.)

## Data Files

All data is stored in the `data/` directory:

- `processed_emails.json` - Tracks all processed emails
- `jobs.json` - Database of found job opportunities
- `token.json` - Gmail API authentication token (auto-generated)

## Project Structure

```
gmail-job-parser/
├── main.py                 # Main execution script
├── config.py              # Configuration settings
├── gmail_client.py        # Gmail API integration
├── ollama_parser.py       # Ollama AI integration
├── job_detector.py        # Job detection and management
├── duplicate_tracker.py   # Duplicate detection system
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── credentials.json      # Gmail API credentials (you provide)
└── data/                 # Data directory (auto-created)
    ├── processed_emails.json
    ├── jobs.json
    └── token.json
```

## Example Output

```
2026-01-04 12:00:00 - INFO - Initializing Gmail Job Parser...
2026-01-04 12:00:01 - INFO - Successfully authenticated with Gmail API
2026-01-04 12:00:01 - INFO - Connected to Ollama. Available models: ['llama3.2']
2026-01-04 12:00:02 - INFO - Starting email processing...
2026-01-04 12:00:02 - INFO - Found 45 messages matching query
2026-01-04 12:00:03 - INFO - Processing email 1/45: Senior Software Engineer Position...
2026-01-04 12:00:05 - INFO - ✓ Email is job-related, extracting details...
2026-01-04 12:00:07 - INFO - ✓ Extracted job: Senior Software Engineer at TechCorp

============================================================
PROCESSING SUMMARY
============================================================
Total emails processed: 45
New job opportunities found: 12
Application confirmations: 3
Duplicates skipped: 18
Non-job emails: 12
============================================================

OVERALL STATISTICS
============================================================
Total emails ever processed: 234
Total job emails: 89
Total confirmations: 15
Total jobs in database: 67
============================================================
```

## Troubleshooting

### Ollama Connection Issues

```bash
# Make sure Ollama is running
ollama serve

# Check if models are available
ollama list

# Pull missing models
ollama pull llama3.2
```

### Gmail API Issues

1. **Missing credentials.json**: Download from Google Cloud Console
2. **Token expired**: Delete `data/token.json` and re-authenticate
3. **API not enabled**: Enable Gmail API in Google Cloud Console

### Model Performance

- **Slow processing**: Try using smaller models like `llama3.2:1b`
- **Inaccurate results**: Try larger models like `llama3.1:70b`
- **Out of memory**: Reduce max_emails or use smaller models

## Advanced Usage

### Custom Job Query

Create a highly specific query to find relevant jobs:

```bash
python main.py --query "(from:linkedin.com OR from:indeed.com OR from:glassdoor.com) AND (Python OR Software Engineer) AND -unsubscribe"
```

### Multiple Model Strategy

Use specialized models for better results:

```bash
# Fast model for detection, accurate model for extraction
export OLLAMA_JOB_DETECTION_MODEL="llama3.2:1b"
export OLLAMA_JOB_EXTRACTION_MODEL="llama3.1:8b"
export OLLAMA_CONFIRMATION_MODEL="llama3.2:1b"

python main.py --max-emails 100
```

### Scheduled Processing

Set up a cron job to run automatically:

```bash
# Add to crontab (runs daily at 9 AM)
0 9 * * * cd /path/to/gmail-job-parser && /path/to/venv/bin/python main.py --max-emails 50
```

## Security Notes

- `credentials.json` contains sensitive OAuth credentials - do not commit to git
- `token.json` contains your access token - keep it secure
- Add to `.gitignore`:
  ```
  credentials.json
  data/token.json
  data/*.json
  ```

## Contributing

Contributions are welcome! Areas for improvement:
- Additional AI models support
- Better job matching algorithms
- Web interface
- Email notifications
- Integration with job boards

## License

This project is provided as-is for personal use.

## Support

For issues or questions:
1. Check Ollama is running and models are pulled
2. Verify Gmail API credentials are correct
3. Check logs for detailed error messages
4. Ensure Python dependencies are installed

## Acknowledgments

- Uses [Ollama](https://ollama.ai) for local AI inference
- Gmail API for email access
- Built for automated job hunting efficiency
