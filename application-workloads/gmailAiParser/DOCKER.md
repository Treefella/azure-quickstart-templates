# Docker Deployment Guide

Complete guide for running Gmail Job Parser with Ollama in Docker containers.

## Quick Start

```bash
# 1. Start Ollama and initialize models
docker-compose up -d ollama ollama-init

# 2. Wait for models to download (check logs)
docker-compose logs -f ollama-init

# 3. Test Ollama models
docker-compose run --rm job-parser python test_ollama_models.py

# 4. Run the job parser
docker-compose run --rm job-parser python main.py --max-emails 50
```

## Architecture

The Docker setup includes three services:

### 1. **ollama** - Ollama LLM Server
- Runs Ollama API server
- Exposes port 11434
- Persistent model storage in Docker volume

### 2. **ollama-init** - Model Initialization
- Runs once on startup
- Pulls required Ollama models
- Configurable via environment variables

### 3. **job-parser** - Gmail Job Parser Application
- Python application
- Connects to Ollama service
- Processes Gmail emails

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 10GB free disk space (for Ollama models)
- Gmail API credentials (`credentials.json`)

## Setup Instructions

### 1. Get Gmail API Credentials

Follow the [QUICKSTART.md](QUICKSTART.md) guide to:
1. Enable Gmail API
2. Create OAuth credentials
3. Download `credentials.json`
4. Place it in this directory

### 2. Configure Models

Edit `docker-compose.yml` to use different models:

```yaml
environment:
  - OLLAMA_JOB_DETECTION_MODEL=llama3.2      # Fast detection
  - OLLAMA_JOB_EXTRACTION_MODEL=llama3.1:8b  # Accurate extraction
  - OLLAMA_CONFIRMATION_MODEL=llama3.2       # Quick confirmation
```

Available models:
- `llama3.2` - Fast, good balance (recommended)
- `llama3.2:1b` - Fastest, less accurate
- `llama3.1:8b` - Slower, more accurate
- `mistral` - Alternative model
- `llama3.1:70b` - Best accuracy, requires GPU

### 3. Start Services

```bash
# Start Ollama server
docker-compose up -d ollama

# Wait for Ollama to be healthy
docker-compose ps

# Initialize models (this takes 5-10 minutes)
docker-compose up ollama-init

# Check initialization logs
docker-compose logs -f ollama-init
```

### 4. Verify Setup

```bash
# Test Ollama connection and models
docker-compose run --rm job-parser python test_ollama_models.py

# Expected output:
# ✓ Connected to Ollama
# ✓ Job posting correctly identified
# ✓ Application confirmation correctly identified
# 🎉 All tests passed!
```

## Usage

### Process Emails

```bash
# Process 50 emails
docker-compose run --rm job-parser python main.py --max-emails 50

# Use custom query
docker-compose run --rm job-parser python main.py \
  --query "from:linkedin.com OR from:indeed.com"

# Process specific number
docker-compose run --rm job-parser python main.py --max-emails 100
```

### View Results

```bash
# List all jobs
docker-compose run --rm job-parser python main.py --list-jobs

# Show statistics
docker-compose run --rm job-parser python main.py --stats-only

# Export to CSV
docker-compose run --rm job-parser python main.py --export jobs.csv

# View exported file
cat data/jobs.csv
```

### Interactive Shell

```bash
# Start interactive Python shell
docker-compose run --rm job-parser python

# Or bash shell
docker-compose run --rm job-parser bash
```

## Data Persistence

All data is stored in the `./data` directory (mounted as volume):

```
data/
├── processed_emails.json   # Processed email tracking
├── jobs.json              # Found job opportunities
├── token.json            # Gmail API token (auto-generated)
└── *.csv                 # Exported job data
```

This directory is mounted to both host and container, so data persists between runs.

## Model Management

### List Available Models

```bash
docker exec gmail-job-parser-ollama ollama list
```

### Pull Additional Models

```bash
# Pull a specific model
docker exec gmail-job-parser-ollama ollama pull mistral

# Pull larger model
docker exec gmail-job-parser-ollama ollama pull llama3.1:8b
```

### Remove Models

```bash
# Remove a model to free space
docker exec gmail-job-parser-ollama ollama rm llama3.2:1b
```

### Model Storage Location

Models are stored in the `ollama_models` Docker volume:

```bash
# Inspect volume
docker volume inspect gmail-job-parser_ollama_models

# Remove all models (WARNING: destructive)
docker-compose down -v
```

## Troubleshooting

### Ollama Not Starting

```bash
# Check Ollama logs
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama

# Check if port is available
netstat -an | grep 11434
```

### Models Not Downloading

```bash
# Check init logs
docker-compose logs ollama-init

# Manually pull model
docker exec gmail-job-parser-ollama ollama pull llama3.2

# Check disk space
docker system df
```

### Gmail Authentication Issues

```bash
# Make sure credentials.json exists
ls -la credentials.json

# Remove old token and re-authenticate
rm data/token.json
docker-compose run --rm job-parser python main.py --max-emails 1
```

### Out of Memory

```bash
# Use smaller models
# Edit docker-compose.yml:
OLLAMA_JOB_DETECTION_MODEL=llama3.2:1b
OLLAMA_JOB_EXTRACTION_MODEL=llama3.2:1b

# Or increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory
```

### Connection Refused

```bash
# Check if Ollama is running
docker-compose ps ollama

# Check Ollama health
docker-compose exec ollama curl http://localhost:11434/api/tags

# Restart services
docker-compose restart
```

## Advanced Configuration

### GPU Support (NVIDIA)

For faster processing with GPU:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Update `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

3. Use larger models:

```yaml
environment:
  - OLLAMA_JOB_EXTRACTION_MODEL=llama3.1:70b
```

### Custom Network

```bash
# Use existing Docker network
docker-compose --network my-network up
```

### Production Deployment

```yaml
# Add restart policies
services:
  ollama:
    restart: always

  job-parser:
    restart: unless-stopped
```

### Scheduled Processing

```bash
# Add to crontab for daily runs
0 9 * * * cd /path/to/gmail-job-parser && docker-compose run --rm job-parser python main.py --max-emails 100
```

## Performance Tuning

### Model Selection by Speed

| Model | Speed | Accuracy | Memory | Best For |
|-------|-------|----------|--------|----------|
| llama3.2:1b | Fastest | Good | 2GB | Quick detection |
| llama3.2 | Fast | Very Good | 4GB | **Recommended** |
| llama3.1:8b | Medium | Excellent | 8GB | Detailed extraction |
| mistral | Medium | Very Good | 6GB | Alternative |
| llama3.1:70b | Slow | Best | 40GB+ | GPU only |

### Optimize for Speed

```yaml
environment:
  # All fast models
  - OLLAMA_JOB_DETECTION_MODEL=llama3.2:1b
  - OLLAMA_JOB_EXTRACTION_MODEL=llama3.2
  - OLLAMA_CONFIRMATION_MODEL=llama3.2:1b
```

### Optimize for Accuracy

```yaml
environment:
  # All accurate models (requires GPU)
  - OLLAMA_JOB_DETECTION_MODEL=llama3.1:8b
  - OLLAMA_JOB_EXTRACTION_MODEL=llama3.1:70b
  - OLLAMA_CONFIRMATION_MODEL=llama3.1:8b
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ollama
docker-compose logs -f job-parser

# Last 100 lines
docker-compose logs --tail 100 ollama
```

### Check Resource Usage

```bash
# Container stats
docker stats gmail-job-parser-ollama gmail-job-parser-app

# Disk usage
docker system df
```

### Health Checks

```bash
# Ollama health
curl http://localhost:11434/api/tags

# In container
docker-compose exec ollama curl http://localhost:11434/api/tags
```

## Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: deletes models and data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker-compose down -v --rmi all
docker system prune -a
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Job Parser

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Start Ollama
        run: docker-compose up -d ollama ollama-init

      - name: Wait for models
        run: docker-compose logs -f ollama-init

      - name: Run tests
        run: docker-compose run --rm job-parser python test_ollama_models.py
```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify Ollama health: `curl http://localhost:11434/api/tags`
3. Test models: `docker-compose run --rm job-parser python test_ollama_models.py`
4. See main [README.md](README.md) for application help

## Next Steps

- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Full documentation
- `example_usage.py` - Python API examples
- `test_ollama_models.py` - Model testing
