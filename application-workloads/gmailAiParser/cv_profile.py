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

    def save_to_file(self, profile_file: str):
        """Save profile to JSON file"""
        data = {
            'skills': list(self.skills),
            'keywords': list(self.keywords),
            'preferred_roles': list(self.preferred_roles),
            'technologies': list(self.technologies),
            'domains': list(self.domains),
            'name': self.profile_data.get('name', ''),
            'description': self.profile_data.get('description', '')
        }

        with open(profile_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved CV profile to {profile_file}")

    def add_skill(self, skill: str):
        """Add a skill to the profile"""
        self.skills.add(skill.lower())

    def add_technology(self, technology: str):
        """Add a technology to the profile"""
        self.technologies.add(technology.lower())

    def add_preferred_role(self, role: str):
        """Add a preferred job role"""
        self.preferred_roles.add(role.lower())

    def add_domain(self, domain: str):
        """Add a domain/industry"""
        self.domains.add(domain.lower())

    def get_all_keywords(self) -> Set[str]:
        """Get all keywords from all categories"""
        all_keywords = set()
        all_keywords.update(self.skills)
        all_keywords.update(self.keywords)
        all_keywords.update(self.preferred_roles)
        all_keywords.update(self.technologies)
        all_keywords.update(self.domains)
        return all_keywords

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

    def get_gmail_query(self) -> str:
        """
        Generate a Gmail query based on CV profile keywords

        Returns:
            Gmail search query string
        """
        # Use top keywords for search
        keywords = []

        # Add preferred roles
        keywords.extend(list(self.preferred_roles)[:5])

        # Add top technologies
        keywords.extend(list(self.technologies)[:5])

        # Add domains
        keywords.extend(list(self.domains)[:3])

        # Create OR query
        if keywords:
            query_parts = [f'"{kw}"' for kw in keywords[:10]]  # Limit to 10 keywords
            return f"({' OR '.join(query_parts)}) AND (job OR position OR opportunity OR hiring)"
        else:
            return "job OR position OR opportunity OR hiring"

    def __str__(self):
        """String representation of profile"""
        return f"""CV Profile:
  Skills: {len(self.skills)} ({', '.join(list(self.skills)[:5])}{', ...' if len(self.skills) > 5 else ''})
  Technologies: {len(self.technologies)} ({', '.join(list(self.technologies)[:5])}{', ...' if len(self.technologies) > 5 else ''})
  Preferred Roles: {len(self.preferred_roles)} ({', '.join(list(self.preferred_roles)[:3])}{', ...' if len(self.preferred_roles) > 3 else ''})
  Domains: {len(self.domains)} ({', '.join(list(self.domains)[:3])}{', ...' if len(self.domains) > 3 else ''})
"""


# Preset profiles for common roles

def create_euc_profile() -> CVProfile:
    """Create End User Computing (EUC) specialist profile"""
    profile = CVProfile()

    # EUC-specific skills
    profile.skills.update([
        'desktop support', 'endpoint management', 'user support',
        'troubleshooting', 'system administration', 'help desk',
        'technical support', 'desktop engineering', 'endpoint security',
        'patch management', 'software deployment', 'imaging',
        'active directory', 'group policy', 'powershell scripting'
    ])

    # EUC technologies
    profile.technologies.update([
        'windows 10', 'windows 11', 'macos', 'vmware horizon',
        'citrix', 'microsoft endpoint manager', 'intune', 'sccm',
        'jamf', 'ivanti', 'tanium', 'microsoft 365', 'azure ad',
        'workspace one', 'parallels', 'rdp', 'vpn', 'office 365',
        'teams', 'zoom', 'slack', 'okta', 'duo security'
    ])

    # Preferred job roles
    profile.preferred_roles.update([
        'euc engineer', 'euc administrator', 'euc specialist',
        'end user computing', 'desktop engineer', 'desktop administrator',
        'endpoint engineer', 'client engineer', 'workspace engineer',
        'vdi engineer', 'vdi administrator', 'citrix administrator',
        'vmware administrator', 'desktop support engineer'
    ])

    # Domains
    profile.domains.update([
        'end user computing', 'desktop management', 'endpoint management',
        'virtual desktop infrastructure', 'vdi', 'desktop virtualization',
        'workspace management', 'client computing'
    ])

    # Additional keywords
    profile.keywords.update([
        'remote work', 'hybrid work', 'digital workspace',
        'user experience', 'end user', 'desktop', 'laptop',
        'mobile device', 'byod', 'zero trust', 'modern workplace'
    ])

    profile.profile_data = {
        'name': 'EUC Specialist',
        'description': 'End User Computing specialist with expertise in desktop/endpoint management, VDI, and modern workplace technologies'
    }

    return profile


def create_devops_profile() -> CVProfile:
    """Create DevOps engineer profile"""
    profile = CVProfile()

    profile.skills.update([
        'ci/cd', 'automation', 'infrastructure as code', 'containerization',
        'orchestration', 'monitoring', 'scripting', 'cloud architecture',
        'devops practices', 'agile', 'version control', 'deployment'
    ])

    profile.technologies.update([
        'docker', 'kubernetes', 'jenkins', 'gitlab', 'github actions',
        'terraform', 'ansible', 'aws', 'azure', 'gcp',
        'prometheus', 'grafana', 'elk stack', 'python', 'bash',
        'git', 'helm', 'argocd', 'vault', 'consul'
    ])

    profile.preferred_roles.update([
        'devops engineer', 'site reliability engineer', 'sre',
        'platform engineer', 'cloud engineer', 'infrastructure engineer',
        'automation engineer', 'build engineer', 'release engineer'
    ])

    profile.domains.update([
        'devops', 'cloud computing', 'infrastructure', 'automation',
        'continuous integration', 'continuous deployment'
    ])

    profile.profile_data = {
        'name': 'DevOps Engineer',
        'description': 'DevOps engineer with expertise in containerization, cloud infrastructure, and automation'
    }

    return profile
