# CV Profiles for Job Matching

This directory contains CV profile JSON files used for keyword-based job matching and relevance scoring.

## What are CV Profiles?

CV profiles define your skills, technologies, preferred roles, and domains. The job parser uses these to:
- Generate targeted Gmail search queries
- Score jobs based on relevance to your profile
- Rank jobs by match percentage
- Identify which of your skills are most in-demand

## Available Profiles

### EUC (End User Computing) Specialist
**File:** `euc_profile.json`

Profile for End User Computing professionals with expertise in:
- Desktop/endpoint management
- VDI (VMware Horizon, Citrix)
- Microsoft technologies (Intune, SCCM, M365)
- Workspace management
- Modern workplace technologies

**Example usage:**
```bash
python search_euc_jobs.py
```

## Creating Your Own Profile

Create a JSON file with this structure:

```json
{
  "name": "Your Profile Name",
  "description": "Brief description of your expertise",
  "skills": [
    "skill 1",
    "skill 2",
    "skill 3"
  ],
  "technologies": [
    "technology 1",
    "technology 2",
    "technology 3"
  ],
  "preferred_roles": [
    "job title 1",
    "job title 2",
    "job title 3"
  ],
  "domains": [
    "industry/domain 1",
    "industry/domain 2"
  ],
  "keywords": [
    "additional keyword 1",
    "additional keyword 2"
  ]
}
```

### Tips for Creating Profiles

1. **Skills**: Technical and soft skills you possess
   - Example: "python", "docker", "project management"

2. **Technologies**: Specific tools, platforms, frameworks
   - Example: "kubernetes", "aws", "react", "postgresql"

3. **Preferred Roles**: Job titles you're interested in
   - Example: "software engineer", "devops engineer", "sre"

4. **Domains**: Industries or specialization areas
   - Example: "cloud computing", "fintech", "healthcare"

5. **Keywords**: Additional relevant terms
   - Example: "remote", "startup", "enterprise"

### Using Your Profile

```python
from cv_profile import CVProfile

# Load your profile
profile = CVProfile('profiles/my_profile.json')

# Generate Gmail query
query = profile.get_gmail_query()

# Score a job
relevance = profile.calculate_job_relevance(job_data)
print(f"Relevance score: {relevance['score']}%")
```

## Scoring System

Jobs are scored based on weighted matches:
- **Preferred Roles**: 30 points per match (most important)
- **Skills**: 20 points per match
- **Technologies**: 15 points per match
- **Domains**: 10 points per match
- **Keywords**: 5 points per match

Scores are normalized to 0-100%:
- **70%+**: Excellent match 🔥
- **50-69%**: Good match ✓
- **30-49%**: Moderate match ○
- **<30%**: Low match -

## Example Profiles for Different Roles

### DevOps Engineer
```python
from cv_profile import create_devops_profile
profile = create_devops_profile()
```

### EUC Specialist
```python
from cv_profile import create_euc_profile
profile = create_euc_profile()
```

## Contributing

Feel free to add more profile examples for different roles:
- Software Engineer
- Data Scientist
- Cloud Architect
- Security Engineer
- Product Manager
- etc.
