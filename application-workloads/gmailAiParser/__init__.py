"""
Gmail Job Parser - Intelligent job opportunity finder using Ollama AI

This package provides tools to automatically parse Gmail emails for job opportunities
using multiple Ollama AI models.
"""

__version__ = "1.0.0"
__author__ = "Gmail Job Parser"

from .gmail_client import GmailClient
from .ollama_parser import OllamaParser
from .job_detector import JobDetector
from .duplicate_tracker import DuplicateTracker

__all__ = [
    'GmailClient',
    'OllamaParser',
    'JobDetector',
    'DuplicateTracker',
]
