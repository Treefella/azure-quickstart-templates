"""
Duplicate email detection and tracking system
"""
import json
import logging
from typing import Dict, List, Set
from pathlib import Path
from datetime import datetime
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class DuplicateTracker:
    """Tracks processed emails and detects duplicates"""

    def __init__(self):
        self.processed_emails_file = config.PROCESSED_EMAILS_FILE
        self.processed_emails: Dict[str, Dict] = {}
        self.load_processed_emails()

    def load_processed_emails(self):
        """Load previously processed emails from file"""
        if self.processed_emails_file.exists():
            try:
                with open(self.processed_emails_file, 'r') as f:
                    self.processed_emails = json.load(f)
                logger.info(f"Loaded {len(self.processed_emails)} processed emails")
            except json.JSONDecodeError as e:
                logger.error(f"Error loading processed emails: {e}")
                self.processed_emails = {}
        else:
            logger.info("No processed emails file found, starting fresh")
            self.processed_emails = {}

    def save_processed_emails(self):
        """Save processed emails to file"""
        try:
            # Ensure data directory exists
            self.processed_emails_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.processed_emails_file, 'w') as f:
                json.dump(self.processed_emails, f, indent=2)
            logger.debug(f"Saved {len(self.processed_emails)} processed emails")
        except Exception as e:
            logger.error(f"Error saving processed emails: {e}")

    def is_processed(self, email_id: str) -> bool:
        """
        Check if an email has already been processed

        Args:
            email_id: Gmail message ID

        Returns:
            True if email was already processed
        """
        return email_id in self.processed_emails

    def mark_as_processed(self, email_id: str, email_data: Dict, is_job: bool = False,
                         is_confirmation: bool = False, job_details: Dict = None):
        """
        Mark an email as processed

        Args:
            email_id: Gmail message ID
            email_data: Email dictionary
            is_job: Whether email is job-related
            is_confirmation: Whether email is application confirmation
            job_details: Extracted job details if applicable
        """
        self.processed_emails[email_id] = {
            'id': email_id,
            'subject': email_data.get('subject', ''),
            'sender': email_data.get('sender', ''),
            'date': email_data.get('date', ''),
            'processed_at': datetime.now().isoformat(),
            'is_job': is_job,
            'is_confirmation': is_confirmation,
            'job_details': job_details
        }

        self.save_processed_emails()

    def find_similar_emails(self, email_data: Dict, similarity_threshold: float = None) -> List[Dict]:
        """
        Find similar emails that were already processed

        Args:
            email_data: Email to compare
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar processed emails
        """
        if similarity_threshold is None:
            similarity_threshold = config.SIMILARITY_THRESHOLD

        similar_emails = []

        # Simple similarity based on subject and sender
        for processed_id, processed_data in self.processed_emails.items():
            score = self._calculate_simple_similarity(email_data, processed_data)

            if score >= similarity_threshold:
                similar_emails.append({
                    'email': processed_data,
                    'similarity_score': score
                })

        return sorted(similar_emails, key=lambda x: x['similarity_score'], reverse=True)

    def _calculate_simple_similarity(self, email1: Dict, email2: Dict) -> float:
        """
        Calculate simple similarity score between two emails

        Args:
            email1: First email
            email2: Second email

        Returns:
            Similarity score (0-1)
        """
        # Check if sender is the same
        sender_match = email1.get('sender', '').lower() == email2.get('sender', '').lower()

        # Calculate subject similarity
        subject1 = set(email1.get('subject', '').lower().split())
        subject2 = set(email2.get('subject', '').lower().split())

        if not subject1 or not subject2:
            return 0.0

        intersection = subject1.intersection(subject2)
        union = subject1.union(subject2)

        subject_similarity = len(intersection) / len(union) if union else 0.0

        # Combine scores
        if sender_match:
            return min(1.0, subject_similarity + 0.3)
        else:
            return subject_similarity

    def get_processed_count(self) -> int:
        """Get total number of processed emails"""
        return len(self.processed_emails)

    def get_job_emails_count(self) -> int:
        """Get count of job-related emails"""
        return sum(1 for email in self.processed_emails.values() if email.get('is_job', False))

    def get_confirmation_emails_count(self) -> int:
        """Get count of application confirmation emails"""
        return sum(1 for email in self.processed_emails.values() if email.get('is_confirmation', False))

    def get_statistics(self) -> Dict:
        """Get statistics about processed emails"""
        total = self.get_processed_count()
        jobs = self.get_job_emails_count()
        confirmations = self.get_confirmation_emails_count()

        return {
            'total_processed': total,
            'job_emails': jobs,
            'confirmation_emails': confirmations,
            'non_job_emails': total - jobs
        }

    def clear_old_entries(self, days: int = 90):
        """
        Remove entries older than specified days

        Args:
            days: Number of days to keep
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.processed_emails)

        self.processed_emails = {
            email_id: data
            for email_id, data in self.processed_emails.items()
            if datetime.fromisoformat(data.get('processed_at', datetime.now().isoformat())) > cutoff_date
        }

        removed = initial_count - len(self.processed_emails)
        if removed > 0:
            logger.info(f"Removed {removed} old entries")
            self.save_processed_emails()
