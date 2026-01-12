"""
Ollama integration for parsing job-related emails
"""
import json
import logging
import requests
from typing import Dict, Optional, List
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class OllamaParser:
    """Parser using Ollama models for job extraction and classification"""

    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.models = config.OLLAMA_MODELS
        self._verify_ollama_connection()

    def _verify_ollama_connection(self):
        """Verify that Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            available_models = [model['name'] for model in response.json().get('models', [])]
            logger.info(f"Connected to Ollama. Available models: {available_models}")

            # Warn if configured models are not available
            for task, model in self.models.items():
                if not any(model in m for m in available_models):
                    logger.warning(f"Model '{model}' for task '{task}' not found. You may need to run: ollama pull {model}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama at {self.base_url}: {e}")
            logger.error("Make sure Ollama is running. You can start it with: ollama serve")

    def _query_ollama(self, model: str, prompt: str, system_prompt: str = None, max_tokens: int = 100) -> Optional[str]:
        """
        Query Ollama model with a prompt

        Args:
            model: Model name to use
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate (lower = faster)

        Returns:
            Model response text
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,  # Deterministic = faster
                    "num_predict": max_tokens  # Limit output length
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300
            )
            response.raise_for_status()

            return response.json().get('response', '').strip()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Ollama model {model}: {e}")
            return None

    def is_job_related(self, email_data: Dict) -> bool:
        """
        Determine if an email is job-related using Ollama

        Args:
            email_data: Email dictionary with subject and body

        Returns:
            True if email is job-related
        """
        # SPEED OPTIMIZATION: Keyword pre-filter before AI call
        text = f"{email_data['subject']} {email_data.get('snippet', '')}".lower()
        has_keywords = any(keyword in text for keyword in config.JOB_KEYWORDS)

        if not has_keywords:
            # No job keywords at all - skip AI call
            return False

        model = self.models['job_detection']

        # Shorter system prompt for speed
        system_prompt = "Identify job-related emails. Reply only YES or NO."

        # Use snippet only (not full body) for speed
        prompt = f"""Subject: {email_data['subject']}
Snippet: {email_data.get('snippet', '')[:200]}

Job email? YES/NO:"""

        response = self._query_ollama(model, prompt, system_prompt, max_tokens=5)

        if response:
            return 'yes' in response.lower()

        # Fallback to keyword matching
        return has_keywords

    def is_application_confirmation(self, email_data: Dict) -> bool:
        """
        Determine if an email is a job application confirmation

        Args:
            email_data: Email dictionary

        Returns:
            True if email is an application confirmation
        """
        model = self.models['confirmation_detection']

        system_prompt = """You are an expert at identifying job application confirmation emails.
These are emails that confirm receipt of a job application, acknowledge submission,
or thank the applicant for applying. Respond with only 'YES' or 'NO'."""

        prompt = f"""Email Subject: {email_data['subject']}

Email Body (first 500 chars):
{email_data['body'][:500]}

Is this a job application confirmation email? Answer with only YES or NO."""

        response = self._query_ollama(model, prompt, system_prompt)

        if response:
            return 'yes' in response.lower()

        # Fallback to keyword matching
        text = f"{email_data['subject']} {email_data['body']}".lower()
        return any(keyword in text for keyword in config.CONFIRMATION_KEYWORDS)

    def extract_job_details(self, email_data: Dict) -> Optional[Dict]:
        """
        Extract structured job information from email using Ollama

        Args:
            email_data: Email dictionary

        Returns:
            Dictionary with extracted job details
        """
        model = self.models['job_extraction']

        # Shorter system prompt for speed
        system_prompt = "Extract job info as JSON. Use null if missing. Return only JSON."

        # Reduced context: 600 chars instead of 2000
        prompt = f"""Subject: {email_data['subject']}
Sender: {email_data['sender']}
Body: {email_data['body'][:600]}

JSON format:
{{"company": "", "position": "", "location": "", "job_type": "", "salary": null, "description": ""}}"""

        response = self._query_ollama(model, prompt, system_prompt, max_tokens=200)

        if response:
            try:
                # Try to extract JSON from response
                start_idx = response.find('{')
                end_idx = response.rfind('}')

                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx + 1]
                    job_details = json.loads(json_str)

                    # Add metadata
                    job_details['email_id'] = email_data['id']
                    job_details['email_subject'] = email_data['subject']
                    job_details['email_sender'] = email_data['sender']
                    job_details['email_date'] = email_data['date']

                    return job_details

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Ollama response: {e}")
                logger.debug(f"Response was: {response}")

        # Return basic details if extraction fails
        return {
            'email_id': email_data['id'],
            'email_subject': email_data['subject'],
            'email_sender': email_data['sender'],
            'email_date': email_data['date'],
            'company': self._extract_company_from_sender(email_data['sender']),
            'position': email_data['subject'],
            'description': email_data['snippet']
        }

    def _extract_company_from_sender(self, sender: str) -> str:
        """Extract company name from email sender"""
        # Try to extract domain or company name from sender
        if '<' in sender and '@' in sender:
            email = sender.split('<')[1].split('>')[0]
            domain = email.split('@')[1]
            company = domain.split('.')[0]
            return company.capitalize()
        elif '@' in sender:
            domain = sender.split('@')[1]
            company = domain.split('.')[0]
            return company.capitalize()
        return sender

    def compare_emails_for_duplicates(self, email1: Dict, email2: Dict) -> float:
        """
        Compare two emails to determine similarity score using Ollama

        Args:
            email1: First email dictionary
            email2: Second email dictionary

        Returns:
            Similarity score between 0 and 1
        """
        model = self.models['job_detection']

        system_prompt = """You are an expert at comparing emails to detect duplicates or similar content.
Compare the two emails and return a similarity score between 0 and 100, where:
- 100 = identical or duplicate emails
- 80-99 = very similar (same job, minor differences)
- 60-79 = similar (related jobs or updates)
- 40-59 = somewhat related
- 0-39 = different emails

Return ONLY a number between 0 and 100."""

        prompt = f"""Email 1:
Subject: {email1['subject']}
Sender: {email1['sender']}
Body preview: {email1['snippet']}

Email 2:
Subject: {email2['subject']}
Sender: {email2['sender']}
Body preview: {email2['snippet']}

Similarity score (0-100):"""

        response = self._query_ollama(model, prompt, system_prompt)

        if response:
            try:
                # Extract number from response
                import re
                numbers = re.findall(r'\d+', response)
                if numbers:
                    score = int(numbers[0])
                    return min(100, max(0, score)) / 100.0
            except (ValueError, IndexError):
                logger.debug(f"Could not parse similarity score from: {response}")

        # Fallback: simple subject comparison
        subject1 = email1['subject'].lower()
        subject2 = email2['subject'].lower()

        if subject1 == subject2:
            return 0.9

        # Count common words
        words1 = set(subject1.split())
        words2 = set(subject2.split())
        common = words1.intersection(words2)

        if len(words1) > 0:
            return len(common) / max(len(words1), len(words2))

        return 0.0
