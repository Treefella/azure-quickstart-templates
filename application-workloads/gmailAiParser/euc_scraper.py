#!/usr/bin/env python3
"""
EUC Job Scraper - Integrates with Gmail Job Parser
Scrapes job boards and saves to PostgreSQL database
"""
import sys
import io
import time
import random
import yaml
import csv
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from bs4 import BeautifulSoup
from rich.table import Table
from rich.live import Live
from rich.console import Console
from rich.panel import Panel

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from db_client import get_db_client
    from cv_profile import CVProfile
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️  Database client not available. CSV output only.")

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_FILE = "euc_config.yaml"

HEADERS_CSV = [
    "title",
    "company",
    "location",
    "date",
    "url",
    "source",
    "relevance_score",
    "priority"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]


class EUCJobScraper:
    """EUC Job Scraper integrated with database"""

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config = self.load_config(config_file)
        self.db_client = None
        self.cv_profile = None
        self.all_jobs = []

        # Initialize database if available
        if DB_AVAILABLE and self.config["output"]["save_to_postgres"]:
            try:
                self.db_client = get_db_client()
                logger.info("✅ Connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                self.db_client = None

        # Load CV profile for relevance scoring
        try:
            self.cv_profile = CVProfile('profiles/graeme_suddick_profile.json')
            logger.info("✅ Loaded CV profile for scoring")
        except Exception as e:
            logger.warning(f"Could not load CV profile: {e}")

    def load_config(self, config_file: str) -> Dict:
        """Load configuration from YAML"""
        try:
            with open(config_file, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            console.print(f"[red]Config file not found: {config_file}[/red]")
            sys.exit(1)

    def build_search_queries(self) -> List[str]:
        """Build search queries from config"""
        queries = []
        for role in self.config["search"]["role_keywords"]:
            # Combine with tech keywords
            tech_str = " ".join(self.config["search"]["tech_keywords"][:3])  # Top 3 only
            q = f'{role} {tech_str}'
            queries.append(q)
        return queries

    def get_headers(self) -> Dict:
        """Get HTTP headers with optional user agent rotation"""
        headers = {}
        if self.config["scraping"]["user_agent_rotation"]:
            headers["User-Agent"] = random.choice(USER_AGENTS)
        else:
            headers["User-Agent"] = USER_AGENTS[0]
        return headers

    def fetch_indeed_jobs(self, query: str, location: str) -> List[Dict]:
        """
        Fetch jobs from Indeed using RSS feed (ethical approach)
        """
        jobs = []
        try:
            # Indeed RSS feed - public API, ethical
            url = f"https://uk.indeed.com/rss?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
            headers = self.get_headers()

            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')

            for item in items[:self.config["scraping"]["max_results_per_query"]]:
                try:
                    job = {
                        "title": item.find('title').text if item.find('title') else "Unknown",
                        "company": item.find('source').text if item.find('source') else "Unknown",
                        "location": item.find('location').text if item.find('location') else location,
                        "date": item.find('pubDate').text if item.find('pubDate') else datetime.utcnow().strftime("%Y-%m-%d"),
                        "url": item.find('link').text if item.find('link') else "",
                        "description": item.find('description').text if item.find('description') else "",
                        "source": "Indeed RSS"
                    }

                    # Check if meets criteria
                    if self.meets_criteria(job):
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching Indeed jobs: {e}")

        return jobs

    def meets_criteria(self, job: Dict) -> bool:
        """Check if job meets filtering criteria"""
        text = f"{job['title']} {job.get('description', '')}".lower()

        # Check exclude keywords
        for keyword in self.config["search"]["exclude_keywords"]:
            if keyword.lower() in text:
                return False

        # Check age if date available
        try:
            if 'date' in job and job['date']:
                job_date = datetime.strptime(job['date'][:10], "%Y-%m-%d")
                max_age = timedelta(days=self.config["search"]["max_job_age_days"])
                if datetime.utcnow() - job_date > max_age:
                    return False
        except:
            pass

        return True

    def score_job(self, job: Dict) -> Dict:
        """Score job relevance using CV profile"""
        if not self.cv_profile:
            return {'score': 0, 'priority': 'check', 'location_match': False}

        job_data = {
            'position': job['title'],
            'company': job['company'],
            'description': job.get('description', ''),
            'location': job['location']
        }

        relevance = self.cv_profile.calculate_job_relevance(job_data)

        # Determine priority
        score = relevance['score']
        location_match = relevance.get('location_match', False)

        if score >= 70 and location_match:
            priority = 'high'
        elif score >= 50:
            priority = 'medium'
        elif score >= 30:
            priority = 'low'
        else:
            priority = 'check'

        return {
            'score': score,
            'priority': priority,
            'location_match': location_match,
            'matched_skills': relevance.get('matched_skills', []),
            'matched_technologies': relevance.get('matched_technologies', []),
            'matched_roles': relevance.get('matched_roles', [])
        }

    def save_to_database(self, job: Dict, relevance: Dict):
        """Save job to PostgreSQL database"""
        if not self.db_client:
            return False

        try:
            job_data = {
                'email_id': f"scraper_{hash(job['url'])}",  # Unique ID
                'company': job['company'],
                'position': job['title'],
                'location': job['location'],
                'description': job.get('description', ''),
                'email_subject': job['title'],
                'email_sender': f"{job['source']} <scraper@jobboard.com>",
                'email_date': datetime.utcnow(),
                'relevance_score': relevance['score'],
                'matched_skills': relevance.get('matched_skills', []),
                'matched_technologies': relevance.get('matched_technologies', []),
                'matched_roles': relevance.get('matched_roles', []),
                'location_match': relevance.get('location_match', False),
                'status': 'new',
                'priority': relevance['priority']
            }

            result = self.db_client.add_job(job_data)
            return result is not None

        except Exception as e:
            logger.error(f"Failed to save job to database: {e}")
            return False

    def save_to_csv(self, job: Dict, relevance: Dict):
        """Save job to CSV file"""
        file_exists = False
        csv_file = self.config["output"]["csv_file"]

        try:
            with open(csv_file, "r"):
                file_exists = True
        except FileNotFoundError:
            pass

        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS_CSV)
            if not file_exists:
                writer.writeheader()

            row = {
                'title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'date': job['date'],
                'url': job['url'][:100],
                'source': job['source'],
                'relevance_score': f"{relevance['score']:.0f}%",
                'priority': relevance['priority']
            }
            writer.writerow(row)

    def render_table(self) -> Table:
        """Render jobs table for real-time display"""
        table = Table(title="🔍 EUC Job Scraper - Real-Time Results", show_header=True)
        table.add_column("Position", style="cyan", width=30)
        table.add_column("Company", style="green", width=20)
        table.add_column("Location", style="yellow", width=15)
        table.add_column("Score", style="magenta", justify="right", width=8)
        table.add_column("Priority", style="blue", width=10)
        table.add_column("Source", style="dim", width=12)

        if not self.all_jobs:
            table.add_row("Searching...", "", "", "", "", "")
            return table

        # Show last 20 jobs
        for job in self.all_jobs[-20:]:
            priority_style = {
                'high': '[red]HIGH[/red]',
                'medium': '[yellow]MEDIUM[/yellow]',
                'low': '[blue]LOW[/blue]',
                'check': '[dim]CHECK[/dim]'
            }.get(job.get('priority', 'check'), 'CHECK')

            table.add_row(
                job['title'][:30],
                job['company'][:20],
                job['location'][:15],
                f"{job.get('relevance_score', 0):.0f}%",
                priority_style,
                job['source'][:12]
            )

        return table

    def run(self):
        """Main scraper loop"""
        console.print(Panel.fit(
            "[bold cyan]EUC Job Scraper[/bold cyan]\n"
            "[dim]Integrated with Gmail Job Parser[/dim]",
            border_style="cyan"
        ))

        queries = self.build_search_queries()
        locations = self.config["search"]["locations"]

        console.print(f"\n📋 Queries: {len(queries)}")
        console.print(f"📍 Locations: {len(locations)}")
        console.print(f"💾 Database: {'✅ Enabled' if self.db_client else '❌ Disabled'}\n")

        with Live(self.render_table(), refresh_per_second=1, console=console) as live:
            for query in queries:
                for location in locations:
                    console.log(f"🔎 Searching: {query} in {location}")

                    # Fetch jobs from Indeed RSS
                    jobs = self.fetch_indeed_jobs(query, location)

                    for job in jobs:
                        # Score job
                        relevance = self.score_job(job)
                        job['relevance_score'] = relevance['score']
                        job['priority'] = relevance['priority']

                        # Save to database
                        if self.db_client:
                            saved = self.save_to_database(job, relevance)
                            if saved:
                                console.log(f"💾 Saved: {job['title']} ({relevance['score']:.0f}%)")

                        # Save to CSV
                        if self.config["output"]["format"] == "csv":
                            self.save_to_csv(job, relevance)

                        # Add to display list
                        self.all_jobs.append(job)

                        # Update display
                        live.update(self.render_table())

                    # Random delay between queries
                    sleep_time = random.randint(
                        self.config["scraping"]["min_delay_seconds"],
                        self.config["scraping"]["max_delay_seconds"]
                    )
                    console.log(f"💤 Sleeping for {sleep_time/60:.1f} minutes")
                    time.sleep(sleep_time)

        # Summary
        console.print(f"\n[green]✅ Scraping complete![/green]")
        console.print(f"   Total jobs found: {len(self.all_jobs)}")
        if self.db_client:
            stats = self.db_client.get_stats()
            console.print(f"   Database jobs: {stats.get('total_jobs', 0)}")
            console.print(f"   High priority: {stats.get('high_priority_jobs', 0)}")


def main():
    scraper = EUCJobScraper()
    scraper.run()


if __name__ == "__main__":
    main()
