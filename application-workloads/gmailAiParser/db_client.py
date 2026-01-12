"""
Database client for Gmail Job Parser with connection pooling
"""
import os
import logging
from contextlib import contextmanager
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import create_engine, desc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from db_models import Base, Job, ProcessedEmail, create_tables

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Database client with connection pooling"""

    def __init__(self, database_url: str = None):
        """
        Initialize database client

        Args:
            database_url: PostgreSQL connection string
                         Format: postgresql://user:password@host:port/database
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://gmail_parser:parser_secure_2024@localhost:5432/gmail_jobs'
        )

        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,  # Number of connections to maintain
            max_overflow=10,  # Maximum overflow connections
            pool_timeout=30,  # Timeout for getting connection
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False  # Set to True for SQL debugging
        )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # Initialize database tables
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        try:
            create_tables(self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions

        Usage:
            with db_client.get_session() as session:
                jobs = session.query(Job).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Job CRUD operations

    def add_job(self, job_data: Dict) -> Optional[Job]:
        """
        Add a new job to database

        Args:
            job_data: Dictionary with job details

        Returns:
            Job object if successful
        """
        try:
            with self.get_session() as session:
                # Check if job with this email_id already exists
                existing = session.query(Job).filter_by(
                    email_id=job_data.get('email_id')
                ).first()

                if existing:
                    logger.debug(f"Job already exists: {job_data.get('email_id')}")
                    return existing

                # Create new job
                job = Job(
                    email_id=job_data.get('email_id'),
                    company=job_data.get('company'),
                    position=job_data.get('position'),
                    location=job_data.get('location'),
                    job_type=job_data.get('job_type'),
                    salary=job_data.get('salary'),
                    description=job_data.get('description'),
                    email_subject=job_data.get('email_subject'),
                    email_sender=job_data.get('email_sender'),
                    email_date=job_data.get('email_date'),
                    relevance_score=job_data.get('relevance_score', 0.0),
                    matched_skills=job_data.get('matched_skills', []),
                    matched_technologies=job_data.get('matched_technologies', []),
                    matched_roles=job_data.get('matched_roles', []),
                    location_match=job_data.get('location_match', False),
                    status=job_data.get('status', 'new'),
                    priority=job_data.get('priority', 'check'),
                    key_requirements=job_data.get('key_requirements', []),
                    application_deadline=job_data.get('application_deadline')
                )

                session.add(job)
                session.flush()
                logger.info(f"Added job: {job.position} at {job.company}")
                return job

        except Exception as e:
            logger.error(f"Failed to add job: {e}")
            return None

    def get_all_jobs(self, status: str = None, limit: int = None) -> List[Job]:
        """
        Get all jobs from database

        Args:
            status: Filter by status (new, applied, rejected, archived)
            limit: Maximum number of jobs to return

        Returns:
            List of Job objects
        """
        try:
            with self.get_session() as session:
                query = session.query(Job)

                if status:
                    query = query.filter_by(status=status)

                query = query.order_by(desc(Job.found_at))

                if limit:
                    query = query.limit(limit)

                return query.all()

        except Exception as e:
            logger.error(f"Failed to get jobs: {e}")
            return []

    def get_job_by_email_id(self, email_id: str) -> Optional[Job]:
        """Get job by email ID"""
        try:
            with self.get_session() as session:
                return session.query(Job).filter_by(email_id=email_id).first()
        except Exception as e:
            logger.error(f"Failed to get job: {e}")
            return None

    def update_job_status(self, email_id: str, status: str) -> bool:
        """Update job status"""
        try:
            with self.get_session() as session:
                job = session.query(Job).filter_by(email_id=email_id).first()
                if job:
                    job.status = status
                    job.updated_at = datetime.utcnow()
                    logger.info(f"Updated job status: {email_id} -> {status}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            return False

    # ProcessedEmail CRUD operations

    def add_processed_email(self, email_data: Dict) -> Optional[ProcessedEmail]:
        """
        Add processed email to database

        Args:
            email_data: Dictionary with email details

        Returns:
            ProcessedEmail object if successful
        """
        try:
            with self.get_session() as session:
                # Check if already processed
                existing = session.query(ProcessedEmail).filter_by(
                    email_id=email_data.get('email_id')
                ).first()

                if existing:
                    return existing

                # Create new processed email record
                processed = ProcessedEmail(
                    email_id=email_data.get('email_id'),
                    subject=email_data.get('subject'),
                    sender=email_data.get('sender'),
                    date=email_data.get('date'),
                    snippet=email_data.get('snippet'),
                    is_job=email_data.get('is_job', False),
                    is_confirmation=email_data.get('is_confirmation', False),
                    is_duplicate=email_data.get('is_duplicate', False),
                    similar_to_email_id=email_data.get('similar_to_email_id'),
                    similarity_score=email_data.get('similarity_score'),
                    processed_by=email_data.get('processed_by', 'ollama')
                )

                session.add(processed)
                session.flush()
                return processed

        except Exception as e:
            logger.error(f"Failed to add processed email: {e}")
            return None

    def is_email_processed(self, email_id: str) -> bool:
        """Check if email has been processed"""
        try:
            with self.get_session() as session:
                exists = session.query(ProcessedEmail).filter_by(
                    email_id=email_id
                ).first() is not None
                return exists
        except Exception as e:
            logger.error(f"Failed to check processed email: {e}")
            return False

    def find_similar_emails(self, email_subject: str, email_sender: str, limit: int = 5) -> List[ProcessedEmail]:
        """
        Find similar processed emails

        Args:
            email_subject: Email subject to search
            email_sender: Email sender to search
            limit: Maximum number of results

        Returns:
            List of similar ProcessedEmail objects
        """
        try:
            with self.get_session() as session:
                # Simple similarity: same sender and similar subject
                results = session.query(ProcessedEmail).filter(
                    and_(
                        ProcessedEmail.sender == email_sender,
                        ProcessedEmail.subject.ilike(f'%{email_subject[:50]}%')
                    )
                ).limit(limit).all()

                return results

        except Exception as e:
            logger.error(f"Failed to find similar emails: {e}")
            return []

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self.get_session() as session:
                total_jobs = session.query(Job).count()
                total_processed = session.query(ProcessedEmail).count()
                job_emails = session.query(ProcessedEmail).filter_by(is_job=True).count()
                high_priority = session.query(Job).filter_by(priority='high').count()

                return {
                    'total_jobs': total_jobs,
                    'total_processed_emails': total_processed,
                    'job_emails': job_emails,
                    'high_priority_jobs': high_priority
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self):
        """Close database connection"""
        self.engine.dispose()
        logger.info("Database connection closed")


# Global database client instance
_db_client = None


def get_db_client() -> DatabaseClient:
    """Get global database client instance"""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client
