"""
Gmail API client for fetching and parsing emails
"""
import base64
import json
import logging
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class GmailClient:
    """Client for interacting with Gmail API"""

    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Authenticate with Gmail API using OAuth2"""
        creds = None

        # Load existing token
        if config.GMAIL_TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(
                str(config.GMAIL_TOKEN_FILE),
                config.GMAIL_SCOPES
            )

        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not config.GMAIL_CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials file not found at {config.GMAIL_CREDENTIALS_FILE}. "
                        "Please download it from Google Cloud Console."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(config.GMAIL_CREDENTIALS_FILE),
                    config.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(config.GMAIL_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully authenticated with Gmail API")

    def fetch_emails(self, query: str = None, max_results: int = None) -> List[Dict]:
        """
        Fetch emails from Gmail based on query

        Args:
            query: Gmail search query (defaults to config.GMAIL_QUERY)
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries with id, subject, body, sender, date
        """
        if query is None:
            query = config.GMAIL_QUERY
        if max_results is None:
            max_results = config.GMAIL_MAX_RESULTS

        try:
            # Get list of message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                logger.info("No messages found matching query")
                return []

            logger.info(f"Found {len(messages)} messages matching query")

            # Fetch full message details
            emails = []
            for msg in messages:
                email_data = self.get_email_details(msg['id'])
                if email_data:
                    emails.append(email_data)

            return emails

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return []

    def get_email_details(self, message_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific email

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            headers = message['payload']['headers']

            # Extract headers
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Extract body
            body = self._get_email_body(message['payload'])

            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }

        except HttpError as error:
            logger.error(f"Error fetching email {message_id}: {error}")
            return None

    def _get_email_body(self, payload: Dict) -> str:
        """
        Extract email body from payload

        Args:
            payload: Email payload from Gmail API

        Returns:
            Email body text
        """
        body = ""

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body += base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not body:
                    # Use HTML if plain text not available
                    if 'data' in part['body']:
                        body += base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                elif 'parts' in part:
                    # Recursively handle nested parts
                    body += self._get_email_body(part)
        else:
            if 'body' in payload and 'data' in payload['body']:
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8', errors='ignore')

        return body

    def mark_as_read(self, message_id: str):
        """Mark an email as read"""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except HttpError as error:
            logger.error(f"Error marking email as read: {error}")
