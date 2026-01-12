# Quick Start Guide

Get the Gmail Job Parser running in 5 minutes!

## Prerequisites
- Python 3.8+
- Gmail account
- 10 minutes to set up Gmail API

## Step 1: Install Ollama (2 minutes)

### Linux/Mac
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows
Download from [ollama.ai](https://ollama.ai)

### Start Ollama
```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull the AI model
ollama pull llama3.2
```

## Step 2: Set Up Gmail API (5 minutes)

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a Project**: Click "Select a project" → "New Project"
3. **Enable Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. **Create Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app"
   - Download the JSON file
5. **Save credentials**: Rename downloaded file to `credentials.json` and place in this directory

## Step 3: Install Python Dependencies (1 minute)

```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 4: Run the Parser (1 minute)

```bash
# Process your first 10 emails
python main.py --max-emails 10
```

On first run, it will:
1. Open your browser to authorize Gmail access
2. Save the authorization for future use
3. Start processing emails!

## What Happens Next?

The parser will:
- ✓ Scan your Gmail for job-related emails
- ✓ Extract job details (company, position, location, salary, etc.)
- ✓ Identify application confirmation emails
- ✓ Skip duplicates automatically
- ✓ Save everything to `data/jobs.json`

## View Your Jobs

```bash
# See all found jobs
python main.py --list-jobs

# Export to CSV
python main.py --export my_jobs.csv

# Show statistics
python main.py --stats-only
```

## Troubleshooting

### "Ollama connection failed"
```bash
# Make sure Ollama is running
ollama serve

# Check if model is available
ollama list

# Pull the model if needed
ollama pull llama3.2
```

### "credentials.json not found"
- Make sure you downloaded and renamed the file correctly
- It should be in the same directory as `main.py`

### "No emails found"
Try a custom query:
```bash
python main.py --query "job OR hiring OR career"
```

## Next Steps

### Process More Emails
```bash
# Process 50 emails
python main.py --max-emails 50

# Process all job emails
python main.py --max-emails 500
```

### Use Different Models
```bash
# Use a larger, more accurate model
export OLLAMA_JOB_EXTRACTION_MODEL="llama3.1:8b"
ollama pull llama3.1:8b
python main.py
```

### Search Specific Sources
```bash
# Only LinkedIn and Indeed
python main.py --query "from:linkedin.com OR from:indeed.com"

# Specific job types
python main.py --query "Python developer OR software engineer"
```

### Schedule Regular Scans
Add to crontab for daily runs:
```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/gmail-job-parser && ./venv/bin/python main.py --max-emails 50
```

## Understanding the Output

```
Processing email 1/45: Senior Software Engineer Position...
✓ Email is job-related, extracting details...
✓ Extracted job: Senior Software Engineer at TechCorp
```

- ✓ **Green checkmark**: Successfully processed
- **Email is job-related**: AI detected this is a job posting
- **Extracting details**: Pulling structured information
- **Application confirmation**: Email confirms you applied

## Tips for Best Results

1. **Let it run on many emails first** - The more emails it processes, the better duplicate detection works
2. **Use specific queries** - Filter by company, role, or source for focused results
3. **Check confirmations** - Review application confirmations to track what you've already applied to
4. **Export regularly** - Export to CSV to analyze trends and opportunities

## Need Help?

See the full [README.md](README.md) for:
- Detailed configuration options
- Advanced usage examples
- Multiple model strategies
- Troubleshooting guide

Happy job hunting! 🎯
