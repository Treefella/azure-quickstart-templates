# ============================================================
# EUC Job Scraper Setup
# ============================================================

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "EUC Job Board Scraper Setup" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

cd C:\users\gls\Documents\gmailAiParser

# Install dependencies
Write-Host "📦 Installing scraper dependencies..." -ForegroundColor Yellow
py -m pip install beautifulsoup4 lxml pyyaml

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed`n" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies`n" -ForegroundColor Red
    exit 1
}

# Check if config exists
if (!(Test-Path "euc_config.yaml")) {
    Write-Host "⚠️  euc_config.yaml not found. Creating default..." -ForegroundColor Yellow

    @"
search:
  role_keywords:
    - "EUC Engineer"
    - "Windows Engineer"
    - "Deployment Engineer"
    - "SCCM Engineer"
    - "Intune Engineer"

  tech_keywords:
    - "Intune"
    - "Autopilot"
    - "SCCM"
    - "Windows 11"
    - "Microsoft 365"

  exclude_keywords:
    - "1st Line"
    - "Service Desk"
    - "Helpdesk"

  locations:
    - "Newcastle"
    - "Durham"
    - "Remote"
    - "North East"

  max_job_age_days: 7

scraping:
  min_delay_seconds: 3600
  max_delay_seconds: 5400
  user_agent_rotation: true
  max_results_per_query: 20

output:
  format: "database"
  csv_file: "euc_jobs.csv"
  realtime_display: true
  save_to_postgres: true
"@ | Out-File -FilePath euc_config.yaml -Encoding UTF8

    Write-Host "✅ Created euc_config.yaml`n" -ForegroundColor Green
}

# Check database
Write-Host "🔍 Checking database connection..." -ForegroundColor Yellow
$dbTest = py -c "from db_client import get_db_client; db = get_db_client(); print('OK')" 2>&1

if ($dbTest -match "OK") {
    Write-Host "✅ Database connected`n" -ForegroundColor Green
} else {
    Write-Host "⚠️  Database not available. Will use CSV output only.`n" -ForegroundColor Yellow
}

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "🚀 Run the scraper:" -ForegroundColor Yellow
Write-Host "   py euc_scraper.py`n" -ForegroundColor Cyan

Write-Host "📝 Edit config:" -ForegroundColor Yellow
Write-Host "   notepad euc_config.yaml`n" -ForegroundColor Cyan

Write-Host "👀 Monitor database:" -ForegroundColor Yellow
Write-Host "   py monitor_db.py`n" -ForegroundColor Cyan

Write-Host "============================================================`n" -ForegroundColor Cyan
