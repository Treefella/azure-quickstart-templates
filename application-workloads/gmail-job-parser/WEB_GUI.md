# Web GUI Usage Guide

## Overview

The web GUI provides a modern, browser-based interface for managing job applications. It's cross-platform and works on Windows, Ubuntu, or any system with a web browser.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Web GUI
```bash
python web_gui.py
```

The GUI will automatically open in your default browser at `http://localhost:5000`

## Features

### Dashboard Overview
- **Job List**: All detected jobs sorted by relevance score
- **Priority Badges**: Visual indicators for job priority
  - 🔴 **High Priority**: 70%+ match + preferred location
  - 🟠 **Medium Priority**: 50-70% match
  - 🟡 **Low Priority**: 30-50% match
  - ⚪ **Check**: <30% match (manual review recommended)

### Filtering
**Left Sidebar Filters:**
- **Priority**: Filter by High/Medium/Low/Check
- **Location**: Filter by preferred locations (Remote, Durham, Newcastle, etc.)
- **Search**: Free-text search across position, company, location, and skills

### Job Details
**Click any job to view:**
- Full position details
- Company information
- Location and contract type
- Rate/salary information (if available)
- Matched skills and technologies
- Original email link
- Full job description

### Actions

**Fetch New Jobs**
- Fetches new emails from Gmail
- Processes them through Ollama
- Scores based on your CV profile
- Updates the job list in real-time

**Export to CSV**
- Exports currently filtered jobs
- Includes all job details
- Filtered by current priority/location/search settings
- Downloads as `jobs_export.csv`

**View Profile**
- Shows your CV profile details
- Skills, technologies, preferred roles
- Location preferences
- Contract preferences (rate, IR35)
- Exclusions

## File Locations

- **Jobs Data**: `data/jobs.json` - All detected jobs
- **Processed Emails**: `data/processed_emails.json` - Duplicate tracking
- **CV Profile**: `profiles/graeme_suddick_profile.json` - Your preferences

## Configuration

The web GUI uses your existing configuration:
- **Ollama URL**: `http://localhost:11434` (configurable in `config.py`)
- **Gmail API**: Uses `credentials.json` and `token.json`
- **CV Profile**: Loads from `profiles/graeme_suddick_profile.json`

## Troubleshooting

### Port Already in Use
If port 5000 is already taken, edit `web_gui.py`:
```python
app.run(debug=True, port=5001)  # Change port number
```

### Browser Doesn't Auto-Open
Manually navigate to: `http://localhost:5000`

### No Jobs Showing
1. Ensure you've run `python main.py` at least once to fetch initial jobs
2. Check that `data/jobs.json` exists and contains job data
3. Click "Fetch New Jobs" to pull from Gmail

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve` or Docker container
- Check Ollama URL in `config.py`
- Test connection: `curl http://localhost:11434/api/tags`

### Gmail API Not Working
- Ensure `credentials.json` is in the project root
- Run `python main.py` first to complete OAuth flow
- Check that `token.json` was created

## Comparison: Web GUI vs Desktop GUI vs CLI

| Feature | Web GUI | Desktop GUI | CLI |
|---------|---------|-------------|-----|
| Platform | Any (browser) | Windows/Linux | Any |
| Installation | Flask only | tkinter | None |
| UI Quality | Modern, responsive | Basic | Text-only |
| Filtering | Real-time | Basic | Limited |
| Export | CSV | JSON/CSV | JSON/CSV |
| Auto-refresh | Yes | Manual | Manual |
| Remote Access | Possible | No | SSH only |

## Advanced Usage

### Running on Different Host/Port
```python
# In web_gui.py, modify the last line:
app.run(host='0.0.0.0', port=8080, debug=False)
```

### Access from Other Devices
If running on a server:
1. Set host to `0.0.0.0`
2. Access via: `http://your-server-ip:5000`
3. Ensure firewall allows port 5000

### Production Deployment
For production use, consider:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_gui:app
```

## API Endpoints

The web GUI exposes REST endpoints:

- `GET /api/jobs` - Get all jobs with scores
- `POST /api/filter` - Filter jobs (priority, location, search)
- `POST /api/fetch` - Fetch new jobs from Gmail
- `GET /api/export` - Export filtered jobs to CSV
- `GET /api/profile` - Get CV profile information

### Example API Usage
```bash
# Get all jobs
curl http://localhost:5000/api/jobs

# Filter jobs
curl -X POST http://localhost:5000/api/filter \
  -H "Content-Type: application/json" \
  -d '{"priority": "high", "location": "remote"}'

# Fetch new jobs
curl -X POST http://localhost:5000/api/fetch \
  -H "Content-Type: application/json" \
  -d '{"max_emails": 50}'
```

## Screenshots

### Main Dashboard
```
┌──────────────────────────────────────────────────────────┐
│  Gmail Job Parser                    [Fetch] [Export]    │
├────────────┬─────────────────────────────────────────────┤
│            │  🔴 Senior SCCM Engineer - Remote - £500/day│
│  Filters   │  Company: IT Solutions Ltd                  │
│            │  95% Match   North East                     │
│  Priority  ├─────────────────────────────────────────────┤
│  □ High    │  🟠 Windows 11 Deployment Lead              │
│  □ Medium  │  Company: NHS Trust                         │
│  □ Low     │  68% Match   Durham                         │
│  □ Check   ├─────────────────────────────────────────────┤
│            │  🟡 IT Support Engineer                     │
│  Location  │  Company: Local Council                     │
│  □ Remote  │  42% Match   Newcastle                      │
│  □ Durham  └─────────────────────────────────────────────┘
│  □ Newcastle
│
│  Search
│  [        ]
└────────────┘
```

## Tips

1. **Filter First**: Use priority and location filters before searching
2. **Regular Fetching**: Click "Fetch New Jobs" daily to stay up-to-date
3. **Export High Priority**: Filter to "High" then export for quick review
4. **Check Low Scores**: Sometimes good jobs score low due to missing keywords
5. **Update Profile**: Adjust `graeme_suddick_profile.json` to improve scoring accuracy

## Next Steps

- Set up Gmail API credentials
- Run initial email fetch
- Launch web GUI
- Filter and review jobs
- Export high-priority matches
- Apply to relevant positions!
