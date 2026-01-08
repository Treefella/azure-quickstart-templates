# ============================================================
# Gmail Job Parser - Direct File Update Script
# No git needed - downloads files directly
# ============================================================

$targetDir = "C:\users\gls\Documents\gmailAiParser"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Gmail Job Parser - Direct File Update" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Navigate to target directory
cd $targetDir

Write-Host "📍 Working in: $targetDir`n" -ForegroundColor Cyan

# Backup existing files
Write-Host "💾 Creating backups..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$filesToBackup = @(
    "cv_profile.py",
    "ollama_parser.py",
    "realtime_gui.py",
    "config.py"
)

foreach ($file in $filesToBackup) {
    if (Test-Path $file) {
        Copy-Item $file "$backupDir\$file" -ErrorAction SilentlyContinue
    }
}

Write-Host "✅ Backups saved to: $backupDir`n" -ForegroundColor Green

# Update cv_profile.py with location_match fix
Write-Host "📝 Updating cv_profile.py..." -ForegroundColor Yellow

$cvProfileContent = @'
"""
CV Profile system for keyword-based job matching and relevance scoring
"""
import json
import logging
from typing import Dict, List, Set
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVProfile:
    """CV profile for matching jobs based on skills and keywords"""

    def __init__(self, profile_file: str = None):
        """
        Initialize CV profile

        Args:
            profile_file: Path to JSON profile file (optional)
        """
        self.profile_data = {}
        self.skills = set()
        self.keywords = set()
        self.preferred_roles = set()
        self.technologies = set()
        self.domains = set()

        if profile_file:
            self.load_from_file(profile_file)

    def load_from_file(self, profile_file: str):
        """Load profile from JSON file"""
        try:
            with open(profile_file, 'r') as f:
                self.profile_data = json.load(f)

            # Extract different keyword categories
            self.skills = set(self.profile_data.get('skills', []))
            self.keywords = set(self.profile_data.get('keywords', []))
            self.preferred_roles = set(self.profile_data.get('preferred_roles', []))
            self.technologies = set(self.profile_data.get('technologies', []))
            self.domains = set(self.profile_data.get('domains', []))

            logger.info(f"Loaded CV profile from {profile_file}")
            logger.info(f"  Skills: {len(self.skills)}")
            logger.info(f"  Technologies: {len(self.technologies)}")
            logger.info(f"  Preferred roles: {len(self.preferred_roles)}")

        except FileNotFoundError:
            logger.error(f"Profile file not found: {profile_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing profile JSON: {e}")

    def calculate_job_relevance(self, job_data: Dict) -> Dict:
        """
        Calculate relevance score for a job based on CV profile

        Args:
            job_data: Job dictionary with title, description, requirements, etc.

        Returns:
            Dictionary with score and matched keywords
        """
        # Combine all job text
        job_text = ' '.join([
            str(job_data.get('position', '')),
            str(job_data.get('company', '')),
            str(job_data.get('description', '')),
            str(job_data.get('email_subject', '')),
            str(job_data.get('email_sender', '')),
            ' '.join(job_data.get('key_requirements', []) if isinstance(job_data.get('key_requirements'), list) else [])
        ]).lower()

        # Track matches by category
        matched_skills = set()
        matched_technologies = set()
        matched_roles = set()
        matched_domains = set()
        matched_keywords = set()

        # Check each category
        for skill in self.skills:
            if skill in job_text:
                matched_skills.add(skill)

        for tech in self.technologies:
            if tech in job_text:
                matched_technologies.add(tech)

        for role in self.preferred_roles:
            if role in job_text:
                matched_roles.add(role)

        for domain in self.domains:
            if domain in job_text:
                matched_domains.add(domain)

        for keyword in self.keywords:
            if keyword in job_text:
                matched_keywords.add(keyword)

        # Calculate weighted score
        score = 0
        score += len(matched_roles) * 30  # Roles are most important
        score += len(matched_skills) * 20  # Skills are very important
        score += len(matched_technologies) * 15  # Technologies matter
        score += len(matched_domains) * 10  # Domain knowledge is good
        score += len(matched_keywords) * 5  # General keywords

        # Normalize to 0-100 scale
        max_possible_score = (
            len(self.preferred_roles) * 30 +
            len(self.skills) * 20 +
            len(self.technologies) * 15 +
            len(self.domains) * 10 +
            len(self.keywords) * 5
        )

        normalized_score = (score / max_possible_score * 100) if max_possible_score > 0 else 0

        # Check location match
        location_match = False
        job_location = str(job_data.get('location', '')).lower()

        if job_location:
            # Get preferred locations from profile
            preferred_locations = []
            if 'contract_preferences' in self.profile_data:
                preferred_locations = [loc.lower() for loc in self.profile_data['contract_preferences'].get('locations', [])]

            # Check if job location matches any preferred location
            for pref_loc in preferred_locations:
                if pref_loc in job_location:
                    location_match = True
                    break

        return {
            'score': round(normalized_score, 2),
            'raw_score': score,
            'matched_skills': list(matched_skills),
            'matched_technologies': list(matched_technologies),
            'matched_roles': list(matched_roles),
            'matched_domains': list(matched_domains),
            'matched_keywords': list(matched_keywords),
            'location_match': location_match,
            'total_matches': len(matched_skills) + len(matched_technologies) +
                           len(matched_roles) + len(matched_domains) + len(matched_keywords)
        }
'@

$cvProfileContent | Out-File -FilePath "cv_profile.py" -Encoding UTF8
Write-Host "✅ Updated cv_profile.py with location_match fix`n" -ForegroundColor Green

# Clear Python cache
Write-Host "🧹 Clearing Python cache..." -ForegroundColor Yellow
Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "✅ Cache cleared`n" -ForegroundColor Green

# Verify the fix
Write-Host "✔️  Verifying fix..." -ForegroundColor Yellow
$content = Get-Content "cv_profile.py" -Raw
if ($content -match "'location_match'") {
    Write-Host "✅ location_match fix verified!`n" -ForegroundColor Green
} else {
    Write-Host "❌ Verification failed`n" -ForegroundColor Red
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Update Complete!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "📦 Backup Location: $targetDir\$backupDir`n" -ForegroundColor Cyan

Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Run the web GUI:" -ForegroundColor White
Write-Host "      py realtime_gui.py`n" -ForegroundColor Cyan

Write-Host "   2. Or start PostgreSQL:" -ForegroundColor White
Write-Host "      docker run -d --name gmail-job-parser-postgres -e POSTGRES_DB=gmail_jobs -e POSTGRES_USER=gmail_parser -e POSTGRES_PASSWORD=parser_secure_2024 -p 5432:5432 postgres:16-alpine`n" -ForegroundColor Cyan

Write-Host "============================================================`n" -ForegroundColor Cyan
