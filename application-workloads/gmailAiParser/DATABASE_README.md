# Database Persistence with PostgreSQL

This project now supports persistent storage using PostgreSQL running in Docker.

## 🏗️ Architecture

### Components

1. **PostgreSQL 16** - Database server running in Docker
2. **SQLAlchemy** - Python ORM for database operations
3. **Connection Pooling** - Efficient database connection management
4. **Automatic Migration** - Migrate existing JSON data to PostgreSQL

### Database Schema

#### Jobs Table
Stores all discovered job postings with:
- Company, position, location, salary, job type
- Email metadata (subject, sender, date)
- Relevance scoring (skills matched, technologies, roles)
- Status tracking (new, applied, rejected, archived)
- Priority levels (high, medium, low, check)

#### Processed Emails Table
Tracks all processed emails to avoid duplicates:
- Email ID, subject, sender, date
- Classification (is_job, is_confirmation, is_duplicate)
- Similarity tracking for duplicate detection
- Processing metadata

## 🚀 Quick Start

### Windows (PowerShell)

```powershell
# Navigate to project directory
cd C:\users\gls\Documents\gmailAiParser

# Run the setup script
.\setup_database.ps1
```

The setup script will:
1. ✅ Check Docker is running
2. ✅ Start PostgreSQL and Ollama containers
3. ✅ Wait for database to be ready
4. ✅ Install Python dependencies (SQLAlchemy, psycopg2)
5. ✅ Optionally migrate existing JSON data
6. ✅ Test database connection

### Manual Setup

If you prefer manual setup:

```powershell
# 1. Start containers
docker-compose up -d postgres ollama

# 2. Wait for PostgreSQL to be ready (30 seconds)
Start-Sleep -Seconds 30

# 3. Install dependencies
py -m pip install sqlalchemy psycopg2-binary alembic

# 4. Migrate existing data (optional)
py migrate_to_db.py

# 5. Test connection
py -c "from db_client import get_db_client; print(get_db_client().get_stats())"
```

## 📊 Database Connection

### Connection String

**Default (local Docker):**
```
postgresql://gmail_parser:parser_secure_2024@localhost:5432/gmail_jobs
```

**From Docker container:**
```
postgresql://gmail_parser:parser_secure_2024@postgres:5432/gmail_jobs
```

### Environment Variable

Set custom database URL:
```powershell
$env:DATABASE_URL = "postgresql://user:password@host:port/database"
```

Or in docker-compose.yml:
```yaml
environment:
  - DATABASE_URL=postgresql://gmail_parser:parser_secure_2024@postgres:5432/gmail_jobs
```

## 🔧 Usage

### In Python Code

```python
from db_client import get_db_client

# Get database client
db = get_db_client()

# Add a job
job_data = {
    'email_id': 'abc123',
    'company': 'TechCorp',
    'position': 'Senior Engineer',
    'location': 'Newcastle',
    'relevance_score': 85.5
}
db.add_job(job_data)

# Get all high priority jobs
jobs = db.get_all_jobs(status='new', limit=10)

# Mark email as processed
email_data = {
    'email_id': 'abc123',
    'subject': 'Job opportunity',
    'sender': 'recruiter@techcorp.com',
    'is_job': True
}
db.add_processed_email(email_data)

# Check if email already processed
if db.is_email_processed('abc123'):
    print("Already processed!")

# Get statistics
stats = db.get_stats()
print(f"Total jobs: {stats['total_jobs']}")
```

### Command Line

```powershell
# Get database statistics
py -c "from db_client import get_db_client; import json; print(json.dumps(get_db_client().get_stats(), indent=2))"

# Count jobs
py -c "from db_client import get_db_client; print(f'Jobs: {len(get_db_client().get_all_jobs())}')"

# Get high priority jobs
py -c "from db_client import get_db_client; jobs = [j.to_dict() for j in get_db_client().get_all_jobs()]; import json; print(json.dumps([j for j in jobs if j['priority'] == 'high'], indent=2))"
```

## 🐳 Docker Management

### Start Database
```powershell
docker-compose up -d postgres
```

### Stop Database
```powershell
docker-compose stop postgres
```

### View Logs
```powershell
docker-compose logs -f postgres
```

### Database Shell (psql)
```powershell
docker exec -it gmail-job-parser-postgres psql -U gmail_parser -d gmail_jobs
```

Common psql commands:
```sql
-- List tables
\dt

-- Count jobs
SELECT COUNT(*) FROM jobs;

-- Count processed emails
SELECT COUNT(*) FROM processed_emails;

-- High priority jobs
SELECT position, company, relevance_score FROM jobs WHERE priority = 'high' ORDER BY relevance_score DESC;

-- Recent jobs
SELECT position, company, found_at FROM jobs ORDER BY found_at DESC LIMIT 10;

-- Exit
\q
```

### Reset Database
```powershell
# WARNING: This deletes all data!
docker-compose down -v
docker-compose up -d postgres
```

## 📈 Performance Features

### Connection Pooling
- **Pool size:** 5 connections
- **Max overflow:** 10 additional connections
- **Pool timeout:** 30 seconds
- **Connection recycle:** 1 hour

### Indexes
Optimized for common queries:
- Email ID lookups (unique index)
- Status and date filtering
- Relevance score sorting
- Sender and date combination

### Context Manager
Automatic session management with rollback on error:
```python
with db.get_session() as session:
    # Your database operations
    jobs = session.query(Job).filter_by(status='new').all()
    # Automatic commit on success, rollback on error
```

## 🔄 Migration from JSON

The `migrate_to_db.py` script automatically migrates:

1. **data/jobs_database.json** → `jobs` table
2. **data/processed_emails.json** → `processed_emails` table

**Note:** Original JSON files are preserved (not deleted).

## 🧪 Testing

Test database connection:
```powershell
py -c "from db_client import get_db_client; db = get_db_client(); print('✅ Connected!'); print(db.get_stats())"
```

## ⚠️ Troubleshooting

### Connection Refused
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solution:**
1. Check Docker is running: `docker ps`
2. Check PostgreSQL container: `docker logs gmail-job-parser-postgres`
3. Wait for database to be ready (30 seconds after start)

### Container Not Found
```
Error response from daemon: No such container: gmail-job-parser-postgres
```

**Solution:**
```powershell
docker-compose up -d postgres
```

### Port Already in Use
```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**Solution:**
1. Stop other PostgreSQL instances
2. Or change port in docker-compose.yml:
```yaml
ports:
  - "5433:5432"  # Use 5433 instead
```

Then update DATABASE_URL:
```
postgresql://gmail_parser:parser_secure_2024@localhost:5433/gmail_jobs
```

## 📊 Monitoring

View container stats:
```powershell
docker stats gmail-job-parser-postgres
```

View database size:
```sql
SELECT pg_size_pretty(pg_database_size('gmail_jobs'));
```

View table sizes:
```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🔐 Security

**Default Credentials (Development Only):**
- Username: `gmail_parser`
- Password: `parser_secure_2024`
- Database: `gmail_jobs`

**Production:** Change credentials in:
1. `docker-compose.yml` (environment variables)
2. `config.py` (DATABASE_URL)
3. Or use environment variable: `$env:DATABASE_URL`

## 🎯 Benefits

### vs JSON Files

| Feature | JSON Files | PostgreSQL |
|---------|-----------|------------|
| **Performance** | Slow for large datasets | Fast with indexes |
| **Concurrency** | File locking issues | Multiple connections |
| **Queries** | Load all into memory | SQL queries |
| **Durability** | File corruption risk | ACID transactions |
| **Scalability** | Limited | Highly scalable |
| **Backups** | Manual file copy | pg_dump / automated |

### Current Implementation

- ✅ **Connection pooling** for efficiency
- ✅ **Automatic migrations** from JSON
- ✅ **Context managers** for safety
- ✅ **Indexed queries** for speed
- ✅ **Docker volumes** for persistence
- ✅ **Health checks** for reliability

## 📚 Next Steps

1. **Backup Strategy:** Set up pg_dump cron job
2. **Monitoring:** Add Grafana for visualizations
3. **Replication:** Configure read replicas for scaling
4. **Migrations:** Use Alembic for schema changes

## 🆘 Support

Check logs:
```powershell
# PostgreSQL logs
docker-compose logs postgres

# Application logs
docker-compose logs job-parser
```

Verify setup:
```powershell
.\setup_database.ps1
```
