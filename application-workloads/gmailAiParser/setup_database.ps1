# Setup database for Gmail Job Parser
# This script will start PostgreSQL in Docker and migrate existing data

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Gmail Job Parser - Database Setup" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Step 1: Check if Docker is running
Write-Host "1. Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "   ✅ Docker is running`n" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Step 2: Start PostgreSQL and Ollama
Write-Host "2. Starting PostgreSQL and Ollama containers..." -ForegroundColor Yellow
docker-compose up -d postgres ollama

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Containers started`n" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to start containers" -ForegroundColor Red
    exit 1
}

# Step 3: Wait for PostgreSQL to be ready
Write-Host "3. Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

$retries = 0
$maxRetries = 30

while ($retries -lt $maxRetries) {
    $result = docker exec gmail-job-parser-postgres pg_isready -U gmail_parser 2>&1
    if ($result -match "accepting connections") {
        Write-Host "   ✅ PostgreSQL is ready`n" -ForegroundColor Green
        break
    }
    $retries++
    Write-Host "   ⏳ Waiting... ($retries/$maxRetries)" -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($retries -eq $maxRetries) {
    Write-Host "   ❌ PostgreSQL failed to start" -ForegroundColor Red
    exit 1
}

# Step 4: Install Python dependencies
Write-Host "4. Installing Python dependencies..." -ForegroundColor Yellow
py -m pip install -q sqlalchemy psycopg2-binary alembic

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Dependencies installed`n" -ForegroundColor Green
} else {
    Write-Host "   ❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 5: Check if there's existing data to migrate
Write-Host "5. Checking for existing data..." -ForegroundColor Yellow
if (Test-Path "data\jobs_database.json" -or Test-Path "data\processed_emails.json") {
    Write-Host "   📦 Found existing JSON data" -ForegroundColor Cyan
    Write-Host "`n   Would you like to migrate existing data to PostgreSQL? (Y/N)" -ForegroundColor Yellow
    $migrate = Read-Host

    if ($migrate -eq "Y" -or $migrate -eq "y") {
        Write-Host "`n6. Migrating existing data to database..." -ForegroundColor Yellow
        py migrate_to_db.py

        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Migration complete`n" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Migration failed" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "   ⏭️  Skipping migration`n" -ForegroundColor Gray
    }
} else {
    Write-Host "   ℹ️  No existing data found (fresh installation)`n" -ForegroundColor Gray
}

# Step 6: Test database connection
Write-Host "7. Testing database connection..." -ForegroundColor Yellow
$testScript = @"
import sys
from db_client import get_db_client
try:
    db = get_db_client()
    stats = db.get_stats()
    print(f'✅ Connected! Jobs: {stats.get("total_jobs", 0)}, Emails: {stats.get("total_processed_emails", 0)}')
    sys.exit(0)
except Exception as e:
    print(f'❌ Connection failed: {e}')
    sys.exit(1)
"@

$testScript | py 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n" -ForegroundColor Green
} else {
    Write-Host "`n   ❌ Database connection test failed" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Database Setup Complete!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "📊 Container Status:" -ForegroundColor Yellow
docker ps --filter "name=gmail-job-parser" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Pull the latest code:" -ForegroundColor White
Write-Host "      git pull origin claude/gmail-job-parser-ollama-b3MKI`n" -ForegroundColor Gray

Write-Host "   2. Run the real-time GUI:" -ForegroundColor White
Write-Host "      py realtime_gui.py`n" -ForegroundColor Gray

Write-Host "   3. Check database stats:" -ForegroundColor White
Write-Host "      py -c 'from db_client import get_db_client; print(get_db_client().get_stats())'`n" -ForegroundColor Gray

Write-Host "   4. Stop containers when done:" -ForegroundColor White
Write-Host "      docker-compose down`n" -ForegroundColor Gray

Write-Host "============================================================`n" -ForegroundColor Cyan
