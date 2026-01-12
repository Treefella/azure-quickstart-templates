"""
Database models for Gmail Job Parser using SQLAlchemy
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, DateTime,
    Boolean, Text, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Job(Base):
    """Job posting model"""
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String(255), unique=True, nullable=False, index=True)

    # Job details
    company = Column(String(255))
    position = Column(String(500))
    location = Column(String(255))
    job_type = Column(String(100))
    salary = Column(String(255))
    description = Column(Text)

    # Email metadata
    email_subject = Column(String(500))
    email_sender = Column(String(255))
    email_date = Column(DateTime)
    email_snippet = Column(Text)

    # Relevance scoring
    relevance_score = Column(Float, default=0.0, index=True)
    matched_skills = Column(JSON)  # List of matched skills
    matched_technologies = Column(JSON)  # List of matched technologies
    matched_roles = Column(JSON)  # List of matched roles
    location_match = Column(Boolean, default=False)

    # Status tracking
    status = Column(String(50), default='new', index=True)  # new, applied, rejected, archived
    priority = Column(String(20), default='check', index=True)  # high, medium, low, check

    # Timestamps
    found_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Additional data
    key_requirements = Column(JSON)  # List of requirements
    application_deadline = Column(DateTime)
    notes = Column(Text)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_relevance_priority', 'relevance_score', 'priority'),
        Index('idx_status_found', 'status', 'found_at'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'company': self.company,
            'position': self.position,
            'location': self.location,
            'job_type': self.job_type,
            'salary': self.salary,
            'description': self.description,
            'email_subject': self.email_subject,
            'email_sender': self.email_sender,
            'email_date': self.email_date.isoformat() if self.email_date else None,
            'relevance_score': self.relevance_score,
            'matched_skills': self.matched_skills or [],
            'matched_technologies': self.matched_technologies or [],
            'matched_roles': self.matched_roles or [],
            'location_match': self.location_match,
            'status': self.status,
            'priority': self.priority,
            'found_at': self.found_at.isoformat() if self.found_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'key_requirements': self.key_requirements or [],
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'notes': self.notes
        }


class ProcessedEmail(Base):
    """Processed email tracking model"""
    __tablename__ = 'processed_emails'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String(255), unique=True, nullable=False, index=True)

    # Email metadata
    subject = Column(String(500))
    sender = Column(String(255), index=True)
    date = Column(DateTime, index=True)
    snippet = Column(Text)

    # Classification
    is_job = Column(Boolean, default=False, index=True)
    is_confirmation = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)

    # Duplicate tracking
    similar_to_email_id = Column(String(255), index=True)  # ID of similar email
    similarity_score = Column(Float)  # Similarity score if duplicate

    # Processing metadata
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_by = Column(String(100))  # AI model or method used

    # Additional data
    body_preview = Column(Text)  # First 500 chars of body
    labels = Column(JSON)  # Gmail labels

    __table_args__ = (
        Index('idx_sender_date', 'sender', 'date'),
        Index('idx_job_processed', 'is_job', 'processed_at'),
    )

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'email_id': self.email_id,
            'subject': self.subject,
            'sender': self.sender,
            'date': self.date.isoformat() if self.date else None,
            'snippet': self.snippet,
            'is_job': self.is_job,
            'is_confirmation': self.is_confirmation,
            'is_duplicate': self.is_duplicate,
            'similar_to_email_id': self.similar_to_email_id,
            'similarity_score': self.similarity_score,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processed_by': self.processed_by,
            'labels': self.labels or []
        }


def create_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """Drop all tables from the database"""
    Base.metadata.drop_all(engine)
