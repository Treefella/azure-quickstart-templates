#!/usr/bin/env python3
"""
Gmail Job Parser GUI
Desktop application for viewing and managing job opportunities from Gmail
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime
from pathlib import Path
import threading
import requests

# Import our existing modules
import config
from gmail_client import GmailClient
from job_detector import JobDetector
from cv_profile import CVProfile


class JobParserGUI:
    """Main GUI application for Gmail Job Parser"""

    def __init__(self, root):
        self.root = root
        self.root.title("Gmail Job Parser - Graeme Suddick")
        self.root.geometry("1400x900")

        # Load CV profile
        self.profile = CVProfile('profiles/graeme_suddick_profile.json')

        # Data
        self.jobs = []
        self.filtered_jobs = []
        self.current_job = None

        # Initialize detector (but don't connect yet)
        self.detector = None
        self.gmail_client = None

        # Create UI
        self.create_widgets()
        self.load_existing_jobs()

        # Status
        self.update_status("Ready")

    def create_widgets(self):
        """Create all UI widgets"""

        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top toolbar
        self.create_toolbar(main_container)

        # Main content area (split pane)
        content_pane = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        content_pane.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left panel - Job list
        self.create_job_list_panel(content_pane)

        # Right panel - Job details
        self.create_job_details_panel(content_pane)

        # Bottom status bar
        self.create_status_bar(main_container)

    def create_toolbar(self, parent):
        """Create top toolbar with actions"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Title
        title_label = ttk.Label(
            toolbar,
            text="Gmail Job Parser - Windows/SCCM/Intune/Azure Roles",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(side=tk.LEFT, padx=5)

        # Spacer
        ttk.Frame(toolbar).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Buttons
        ttk.Button(
            toolbar,
            text="🔄 Fetch New Jobs",
            command=self.fetch_new_jobs
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="🔍 Analyze with AI",
            command=self.analyze_selected_job
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="💾 Export CSV",
            command=self.export_to_csv
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="⚙️ Settings",
            command=self.show_settings
        ).pack(side=tk.LEFT, padx=2)

    def create_job_list_panel(self, parent):
        """Create left panel with job list and filters"""
        left_panel = ttk.Frame(parent)
        parent.add(left_panel, weight=1)

        # Filter section
        filter_frame = ttk.LabelFrame(left_panel, text="Filters", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        # Priority filter
        ttk.Label(filter_frame, text="Priority:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.priority_var = tk.StringVar(value="All")
        priority_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.priority_var,
            values=["All", "🔴 High", "🟠 Medium", "🟡 Low", "⚪ Check"],
            state="readonly",
            width=15
        )
        priority_combo.grid(row=0, column=1, sticky=tk.EW, pady=2)
        priority_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Location filter
        ttk.Label(filter_frame, text="Location:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.location_var = tk.StringVar(value="All")
        location_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.location_var,
            values=["All", "Remote", "North East", "Hybrid", "Other"],
            state="readonly",
            width=15
        )
        location_combo.grid(row=1, column=1, sticky=tk.EW, pady=2)
        location_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Contract type filter
        ttk.Label(filter_frame, text="Type:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.contract_var = tk.StringVar(value="All")
        contract_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.contract_var,
            values=["All", "Contract", "Permanent", "Both"],
            state="readonly",
            width=15
        )
        contract_combo.grid(row=2, column=1, sticky=tk.EW, pady=2)
        contract_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Search
        ttk.Label(filter_frame, text="Search:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.apply_filters())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=15)
        search_entry.grid(row=3, column=1, sticky=tk.EW, pady=2)

        filter_frame.columnconfigure(1, weight=1)

        # Statistics
        stats_frame = ttk.Frame(left_panel)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        self.stats_label = ttk.Label(
            stats_frame,
            text="Jobs: 0 | High: 0 | Medium: 0 | Low: 0",
            font=('Arial', 9)
        )
        self.stats_label.pack()

        # Job list
        list_frame = ttk.LabelFrame(left_panel, text="Job Opportunities", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview with scrollbar
        tree_scroll = ttk.Scrollbar(list_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.job_tree = ttk.Treeview(
            list_frame,
            columns=('Priority', 'Title', 'Company', 'Location', 'Score'),
            show='tree headings',
            yscrollcommand=tree_scroll.set,
            selectmode='browse'
        )
        tree_scroll.config(command=self.job_tree.yview)

        # Configure columns
        self.job_tree.heading('#0', text='Date')
        self.job_tree.heading('Priority', text='Priority')
        self.job_tree.heading('Title', text='Job Title')
        self.job_tree.heading('Company', text='Company')
        self.job_tree.heading('Location', text='Location')
        self.job_tree.heading('Score', text='Score')

        self.job_tree.column('#0', width=80, minwidth=80)
        self.job_tree.column('Priority', width=60, minwidth=60)
        self.job_tree.column('Title', width=200, minwidth=150)
        self.job_tree.column('Company', width=120, minwidth=100)
        self.job_tree.column('Location', width=100, minwidth=80)
        self.job_tree.column('Score', width=50, minwidth=50)

        self.job_tree.pack(fill=tk.BOTH, expand=True)
        self.job_tree.bind('<<TreeviewSelect>>', self.on_job_selected)

    def create_job_details_panel(self, parent):
        """Create right panel with job details"""
        right_panel = ttk.Frame(parent)
        parent.add(right_panel, weight=2)

        # Job title and actions
        header_frame = ttk.Frame(right_panel)
        header_frame.pack(fill=tk.X, padx=5, pady=5)

        self.job_title_label = ttk.Label(
            header_frame,
            text="Select a job to view details",
            font=('Arial', 12, 'bold'),
            wraplength=800
        )
        self.job_title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Action buttons
        action_frame = ttk.Frame(header_frame)
        action_frame.pack(side=tk.RIGHT)

        ttk.Button(
            action_frame,
            text="✉️ Open Email",
            command=self.open_email,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            action_frame,
            text="🌐 Apply",
            command=self.open_application,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        # Notebook for tabs
        self.details_notebook = ttk.Notebook(right_panel)
        self.details_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Overview
        overview_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(overview_tab, text="📋 Overview")

        overview_scroll = scrolledtext.ScrolledText(
            overview_tab,
            wrap=tk.WORD,
            font=('Courier', 10),
            height=20
        )
        overview_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.overview_text = overview_scroll

        # Tab 2: AI Analysis
        analysis_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(analysis_tab, text="🤖 AI Analysis")

        analysis_scroll = scrolledtext.ScrolledText(
            analysis_tab,
            wrap=tk.WORD,
            font=('Courier', 10),
            height=20
        )
        analysis_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.analysis_text = analysis_scroll

        # Tab 3: Email Content
        email_tab = ttk.Frame(self.details_notebook)
        self.details_notebook.add(email_tab, text="✉️ Email")

        email_scroll = scrolledtext.ScrolledText(
            email_tab,
            wrap=tk.WORD,
            font=('Courier', 9),
            height=20
        )
        email_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.email_text = email_scroll

    def create_status_bar(self, parent):
        """Create bottom status bar"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(side=tk.RIGHT, padx=5, pady=2)

    def load_existing_jobs(self):
        """Load jobs from existing JSON file"""
        try:
            jobs_file = config.JOBS_DATABASE_FILE

            if jobs_file.exists():
                with open(jobs_file, 'r') as f:
                    self.jobs = json.load(f)

                # Score and categorize jobs
                self.score_and_categorize_jobs()

                self.update_status(f"Loaded {len(self.jobs)} jobs from database")
                self.populate_job_list()
            else:
                self.update_status("No existing jobs found - click 'Fetch New Jobs' to start")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load jobs: {e}")
            self.update_status(f"Error loading jobs: {e}")

    def score_and_categorize_jobs(self):
        """Score jobs based on CV profile and categorize priority"""
        for job in self.jobs:
            # Calculate relevance score
            relevance = self.profile.calculate_job_relevance(job)
            job['relevance_score'] = relevance['score']
            job['matched_skills'] = relevance['matched_skills']
            job['matched_technologies'] = relevance['matched_technologies']
            job['matched_roles'] = relevance['matched_roles']

            # Categorize priority
            job['priority'] = self.categorize_priority(job, relevance)

    def categorize_priority(self, job, relevance):
        """Determine job priority based on relevance and criteria"""
        score = relevance['score']
        location = str(job.get('location', '')).lower()
        contract_type = str(job.get('job_type', '')).lower()

        # Check location preference
        ne_locations = ['remote', 'durham', 'newcastle', 'north east', 'northeast',
                       'sunderland', 'consett', 'gateshead', 'hybrid']
        location_match = any(loc in location for loc in ne_locations)

        # Check contract preference
        is_contract = 'contract' in contract_type or 'contract' in job.get('description', '').lower()

        # Priority logic
        if score >= 70:
            if location_match:
                return "🔴 High"
            return "🟠 Medium"
        elif score >= 50:
            if location_match and is_contract:
                return "🟠 Medium"
            return "🟡 Low"
        elif score >= 30:
            return "🟡 Low"
        else:
            return "⚪ Check"

    def populate_job_list(self):
        """Populate the job treeview"""
        # Clear existing
        for item in self.job_tree.get_children():
            self.job_tree.delete(item)

        # Apply filters
        self.apply_filters()

    def apply_filters(self):
        """Apply current filters to job list"""
        # Start with all jobs
        filtered = self.jobs.copy()

        # Priority filter
        priority = self.priority_var.get()
        if priority != "All":
            filtered = [j for j in filtered if j.get('priority', '') == priority]

        # Location filter
        location = self.location_var.get()
        if location != "All":
            if location == "Remote":
                filtered = [j for j in filtered if 'remote' in str(j.get('location', '')).lower()]
            elif location == "North East":
                ne_locs = ['durham', 'newcastle', 'sunderland', 'north east', 'northeast']
                filtered = [j for j in filtered if any(loc in str(j.get('location', '')).lower() for loc in ne_locs)]
            elif location == "Hybrid":
                filtered = [j for j in filtered if 'hybrid' in str(j.get('location', '')).lower()]

        # Contract type filter
        contract = self.contract_var.get()
        if contract != "All":
            filtered = [j for j in filtered if contract.lower() in str(j.get('job_type', '')).lower()]

        # Search filter
        search = self.search_var.get().lower()
        if search:
            filtered = [j for j in filtered if
                       search in str(j.get('position', '')).lower() or
                       search in str(j.get('company', '')).lower() or
                       search in str(j.get('description', '')).lower()]

        self.filtered_jobs = filtered

        # Update tree
        self.job_tree.delete(*self.job_tree.get_children())

        # Sort by priority and score
        priority_order = {"🔴 High": 0, "🟠 Medium": 1, "🟡 Low": 2, "⚪ Check": 3}
        sorted_jobs = sorted(
            filtered,
            key=lambda x: (priority_order.get(x.get('priority', '⚪ Check'), 3),
                          -x.get('relevance_score', 0))
        )

        for job in sorted_jobs:
            date_str = job.get('found_at', '')[:10] if job.get('found_at') else 'Unknown'

            self.job_tree.insert('', 'end',
                                text=date_str,
                                values=(
                                    job.get('priority', '⚪'),
                                    job.get('position', 'Unknown')[:40],
                                    job.get('company', 'Unknown')[:20],
                                    job.get('location', 'Unknown')[:20],
                                    f"{job.get('relevance_score', 0):.0f}%"
                                ),
                                tags=(job.get('email_id'),))

        # Update statistics
        self.update_statistics()

    def update_statistics(self):
        """Update job statistics"""
        total = len(self.filtered_jobs)
        high = len([j for j in self.filtered_jobs if j.get('priority') == "🔴 High"])
        medium = len([j for j in self.filtered_jobs if j.get('priority') == "🟠 Medium"])
        low = len([j for j in self.filtered_jobs if j.get('priority') == "🟡 Low"])

        self.stats_label.config(
            text=f"Jobs: {total} | 🔴 High: {high} | 🟠 Medium: {medium} | 🟡 Low: {low}"
        )

    def on_job_selected(self, event):
        """Handle job selection in tree"""
        selection = self.job_tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.job_tree.item(item, 'tags')

        if tags:
            email_id = tags[0]
            self.current_job = next((j for j in self.jobs if j.get('email_id') == email_id), None)

            if self.current_job:
                self.display_job_details(self.current_job)

    def display_job_details(self, job):
        """Display selected job details"""
        # Update title
        self.job_title_label.config(text=job.get('position', 'Unknown Position'))

        # Overview tab
        overview = f"""
{'='*70}
JOB DETAILS
{'='*70}

Position: {job.get('position', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Type: {job.get('job_type', 'Unknown')}
Salary/Rate: {job.get('salary', 'Not specified')}

Priority: {job.get('priority', 'Unknown')}
Relevance Score: {job.get('relevance_score', 0):.1f}%

{'='*70}
MATCHED SKILLS
{'='*70}

{', '.join(job.get('matched_skills', [])[:10]) if job.get('matched_skills') else 'None'}

{'='*70}
MATCHED TECHNOLOGIES
{'='*70}

{', '.join(job.get('matched_technologies', [])[:10]) if job.get('matched_technologies') else 'None'}

{'='*70}
DESCRIPTION
{'='*70}

{job.get('description', 'No description available')}

{'='*70}
KEY REQUIREMENTS
{'='*70}

{chr(10).join('• ' + str(req) for req in job.get('key_requirements', [])) if isinstance(job.get('key_requirements'), list) else job.get('key_requirements', 'Not specified')}

"""

        self.overview_text.delete('1.0', tk.END)
        self.overview_text.insert('1.0', overview)

        # Email tab
        email_content = f"""
Subject: {job.get('email_subject', 'Unknown')}
From: {job.get('email_sender', 'Unknown')}
Date: {job.get('email_date', 'Unknown')}

{'-'*70}

{job.get('email_body', 'Email content not available')}
"""

        self.email_text.delete('1.0', tk.END)
        self.email_text.insert('1.0', email_content)

        # AI Analysis tab (placeholder - would need Qwen integration)
        analysis = f"""
AI Analysis with qwen2.5:7b-instruct

Click "🔍 Analyze with AI" button to run detailed analysis.

This will extract:
- IR35 status
- Contract type
- Rate/Salary details
- Start date
- Urgency level
- Skill requirements
- Detailed relevance scoring
"""

        self.analysis_text.delete('1.0', tk.END)
        self.analysis_text.insert('1.0', analysis)

    def fetch_new_jobs(self):
        """Fetch new jobs from Gmail"""
        def fetch_thread():
            try:
                self.progress.start()
                self.update_status("Connecting to Gmail...")

                # Initialize detector if needed
                if not self.detector:
                    self.detector = JobDetector()

                self.update_status("Processing emails...")

                # Process emails
                self.detector.process_emails(max_emails=100)

                # Reload jobs
                self.load_existing_jobs()

                self.update_status(f"Fetched and processed emails successfully")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to fetch jobs: {e}")
                self.update_status(f"Error: {e}")
            finally:
                self.progress.stop()

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()

    def analyze_selected_job(self):
        """Analyze selected job with Qwen AI"""
        if not self.current_job:
            messagebox.showwarning("No Selection", "Please select a job first")
            return

        def analyze_thread():
            try:
                self.progress.start()
                self.update_status("Analyzing with Qwen AI...")

                # Use Qwen for detailed analysis
                analysis = self.analyze_with_qwen(self.current_job)

                if analysis:
                    # Display analysis
                    analysis_text = self.format_ai_analysis(analysis)
                    self.analysis_text.delete('1.0', tk.END)
                    self.analysis_text.insert('1.0', analysis_text)

                    self.update_status("AI analysis complete")
                else:
                    self.update_status("AI analysis failed - check Ollama connection")

            except Exception as e:
                messagebox.showerror("Error", f"AI analysis failed: {e}")
                self.update_status(f"Error: {e}")
            finally:
                self.progress.stop()

        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()

    def analyze_with_qwen(self, job):
        """Use Qwen model for detailed analysis"""
        # This would call the qwen2.5:7b-instruct model
        # Implementation similar to the user's script
        # For now, return None (needs Qwen integration)
        return None

    def format_ai_analysis(self, analysis):
        """Format AI analysis for display"""
        if not analysis:
            return "No analysis available"

        # Format the analysis dict into readable text
        return json.dumps(analysis, indent=2)

    def export_to_csv(self):
        """Export filtered jobs to CSV"""
        if not self.filtered_jobs:
            messagebox.showwarning("No Jobs", "No jobs to export")
            return

        try:
            import csv
            filename = f"jobs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = config.DATA_DIR / filename

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['priority', 'score', 'position', 'company', 'location',
                            'job_type', 'salary', 'matched_skills', 'email_subject']

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()

                for job in self.filtered_jobs:
                    row = job.copy()
                    row['score'] = job.get('relevance_score', 0)
                    row['matched_skills'] = ', '.join(job.get('matched_skills', [])[:5])
                    writer.writerow(row)

            messagebox.showinfo("Success", f"Exported {len(self.filtered_jobs)} jobs to:\n{filepath}")
            self.update_status(f"Exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"Error: {e}")

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")

        ttk.Label(settings_window, text="Settings", font=('Arial', 14, 'bold')).pack(pady=10)

        # CV Profile
        profile_frame = ttk.LabelFrame(settings_window, text="CV Profile", padding=10)
        profile_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(profile_frame, text=f"Profile: {self.profile.profile_data.get('name', 'Unknown')}").pack(anchor=tk.W)
        ttk.Label(profile_frame, text=f"Skills: {len(self.profile.skills)}").pack(anchor=tk.W)
        ttk.Label(profile_frame, text=f"Technologies: {len(self.profile.technologies)}").pack(anchor=tk.W)

        # Close button
        ttk.Button(settings_window, text="Close", command=settings_window.destroy).pack(pady=10)

    def open_email(self):
        """Open email in default client"""
        if not self.current_job:
            return

        messagebox.showinfo("Feature", "Email opening feature - to be implemented")

    def open_application(self):
        """Open job application link"""
        if not self.current_job:
            return

        messagebox.showinfo("Feature", "Application link feature - to be implemented")

    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)
        self.root.update_idletasks()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = JobParserGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
