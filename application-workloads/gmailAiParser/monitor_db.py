#!/usr/bin/env python3
"""
Real-time database monitor - watch records being added to PostgreSQL
"""
import sys
import io
import time
import logging
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich import box

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from db_client import get_db_client
except ImportError:
    print("❌ Database client not found. Make sure db_client.py exists.")
    print("💡 Run: git pull origin claude/gmail-job-parser-ollama-b3MKI")
    sys.exit(1)

# Suppress logs
logging.basicConfig(level=logging.ERROR)

console = Console()


class DatabaseMonitor:
    """Real-time database monitor"""

    def __init__(self):
        self.db_client = None
        self.last_job_count = 0
        self.last_email_count = 0
        self.last_jobs = []
        self.start_time = datetime.now()
        self.connected = False

    def connect(self):
        """Connect to database"""
        try:
            self.db_client = get_db_client()
            stats = self.db_client.get_stats()
            self.last_job_count = stats.get('total_jobs', 0)
            self.last_email_count = stats.get('total_processed_emails', 0)
            self.connected = True
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to connect: {e}[/red]")
            return False

    def get_recent_jobs(self, limit=10):
        """Get most recent jobs"""
        try:
            with self.db_client.get_session() as session:
                from db_models import Job
                from sqlalchemy import desc

                jobs = session.query(Job).order_by(desc(Job.found_at)).limit(limit).all()
                return [j.to_dict() for j in jobs]
        except Exception as e:
            console.print(f"[red]Error getting jobs: {e}[/red]")
            return []

    def create_stats_table(self, stats, new_jobs, new_emails):
        """Create statistics table"""
        table = Table(title="📊 Database Statistics", box=box.ROUNDED, show_header=True)
        table.add_column("Metric", style="cyan", width=30)
        table.add_column("Count", style="green", justify="right", width=15)
        table.add_column("New", style="yellow", justify="right", width=15)

        # Runtime
        runtime = datetime.now() - self.start_time
        runtime_str = str(runtime).split('.')[0]  # Remove microseconds

        table.add_row("⏱️  Runtime", runtime_str, "")
        table.add_row("", "", "")  # Spacer
        table.add_row("💼 Total Jobs", str(stats.get('total_jobs', 0)), f"+{new_jobs}" if new_jobs > 0 else "")
        table.add_row("📧 Processed Emails", str(stats.get('total_processed_emails', 0)), f"+{new_emails}" if new_emails > 0 else "")
        table.add_row("✉️  Job Emails", str(stats.get('job_emails', 0)), "")
        table.add_row("🔥 High Priority", str(stats.get('high_priority_jobs', 0)), "")

        # Calculate rate
        if runtime.total_seconds() > 0:
            jobs_per_min = (stats.get('total_jobs', 0) / runtime.total_seconds()) * 60
            emails_per_min = (stats.get('total_processed_emails', 0) / runtime.total_seconds()) * 60
            table.add_row("", "", "")  # Spacer
            table.add_row("📈 Jobs/min", f"{jobs_per_min:.1f}", "")
            table.add_row("📈 Emails/min", f"{emails_per_min:.1f}", "")

        return table

    def create_jobs_table(self, jobs):
        """Create recent jobs table"""
        table = Table(title="🆕 Recent Jobs (Last 10)", box=box.SIMPLE, show_header=True)
        table.add_column("Position", style="cyan", width=30, no_wrap=False)
        table.add_column("Company", style="green", width=20)
        table.add_column("Score", style="yellow", justify="right", width=8)
        table.add_column("Priority", style="magenta", width=10)
        table.add_column("Time", style="blue", width=20)

        if not jobs:
            table.add_row("No jobs yet...", "", "", "", "")
            return table

        for job in jobs:
            position = job.get('position', 'Unknown')[:30]
            company = job.get('company', 'Unknown')[:20]
            score = f"{job.get('relevance_score', 0):.0f}%"
            priority = job.get('priority', 'check').upper()

            # Format time
            found_at = job.get('found_at', '')
            if found_at:
                try:
                    dt = datetime.fromisoformat(found_at.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = found_at[:19]
            else:
                time_str = ""

            # Color based on priority
            priority_style = {
                'HIGH': '[red]HIGH[/red]',
                'MEDIUM': '[yellow]MEDIUM[/yellow]',
                'LOW': '[blue]LOW[/blue]',
                'CHECK': '[dim]CHECK[/dim]'
            }.get(priority, priority)

            table.add_row(position, company, score, priority_style, time_str)

        return table

    def create_layout(self, stats, new_jobs, new_emails, jobs):
        """Create display layout"""
        layout = Layout()

        # Split into top and bottom
        layout.split_column(
            Layout(name="stats", size=12),
            Layout(name="jobs")
        )

        # Stats table
        stats_table = self.create_stats_table(stats, new_jobs, new_emails)
        layout["stats"].update(Panel(stats_table, title="[bold blue]Real-Time Monitor[/bold blue]", border_style="blue"))

        # Jobs table
        jobs_table = self.create_jobs_table(jobs)
        layout["jobs"].update(Panel(jobs_table, title="[bold green]Latest Jobs[/bold green]", border_style="green"))

        return layout

    def monitor(self, refresh_interval=2):
        """Start monitoring"""
        console.print("\n[bold cyan]🔍 Database Monitor Starting...[/bold cyan]\n")

        if not self.connect():
            console.print("[red]❌ Failed to connect to database[/red]")
            console.print("[yellow]💡 Make sure PostgreSQL is running:[/yellow]")
            console.print("   docker ps --filter name=postgres")
            return

        console.print("[green]✅ Connected to database[/green]")
        console.print(f"[dim]Refresh interval: {refresh_interval} seconds[/dim]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        try:
            with Live(console=console, refresh_per_second=1) as live:
                while True:
                    # Get current stats
                    stats = self.db_client.get_stats()

                    # Calculate new records
                    current_jobs = stats.get('total_jobs', 0)
                    current_emails = stats.get('total_processed_emails', 0)

                    new_jobs = current_jobs - self.last_job_count
                    new_emails = current_emails - self.last_email_count

                    # Get recent jobs
                    jobs = self.get_recent_jobs(10)

                    # Update display
                    layout = self.create_layout(stats, new_jobs, new_emails, jobs)
                    live.update(layout)

                    # Update last counts
                    self.last_job_count = current_jobs
                    self.last_email_count = current_emails

                    # Sleep
                    time.sleep(refresh_interval)

        except KeyboardInterrupt:
            console.print("\n\n[yellow]⏹️  Monitoring stopped[/yellow]")
        except Exception as e:
            console.print(f"\n\n[red]❌ Error: {e}[/red]")


def main():
    """Main function"""
    console.print(Panel.fit(
        "[bold cyan]Database Real-Time Monitor[/bold cyan]\n"
        "[dim]Watch records being added to PostgreSQL in real-time[/dim]",
        border_style="cyan"
    ))

    # Parse refresh interval from command line
    refresh_interval = 2
    if len(sys.argv) > 1:
        try:
            refresh_interval = int(sys.argv[1])
        except ValueError:
            console.print(f"[red]Invalid refresh interval: {sys.argv[1]}[/red]")
            console.print("[yellow]Usage: py monitor_db.py [refresh_interval_seconds][/yellow]")
            return

    monitor = DatabaseMonitor()
    monitor.monitor(refresh_interval)


if __name__ == '__main__':
    main()
