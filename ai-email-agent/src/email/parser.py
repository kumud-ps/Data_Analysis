import re
import html
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import email.utils
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.exceptions import EmailParsingError

logger = get_logger(__name__)


class EmailParser:
    """Utility class for parsing and analyzing email content."""

    def __init__(self):
        """Initialize email parser."""
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})')
        self.date_pattern = re.compile(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b')

        # Action-oriented keywords
        self.action_keywords = [
            'please', 'could you', 'would you', 'can you', 'need', 'help', 'assist',
            'review', 'check', 'look at', 'examine', 'consider', 'approve', 'reject',
            'confirm', 'verify', 'validate', 'schedule', 'arrange', 'organize',
            'contact', 'reach out', 'call', 'email', 'reply', 'respond', 'send'
        ]

        # Urgency indicators
        self.urgency_keywords = [
            'urgent', 'asap', 'immediately', 'right away', 'as soon as possible',
            'emergency', 'critical', 'priority', 'important', 'time sensitive',
            'deadline', 'due today', 'due tomorrow', 'overdue'
        ]

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract various entities from email text."""
        try:
            entities = {
                'urls': self._extract_urls(text),
                'emails': self._extract_emails(text),
                'phone_numbers': self._extract_phone_numbers(text),
                'dates': self._extract_dates(text),
                'mentions': self._extract_mentions(text)
            }
            return entities
        except Exception as e:
            logger.error("Error extracting entities", error=str(e))
            return {'urls': [], 'emails': [], 'phone_numbers': [], 'dates': [], 'mentions': []}

    def analyze_content(self, subject: str, body: str) -> Dict[str, Any]:
        """Analyze email content for key information and characteristics."""
        try:
            full_text = f"{subject} {body}".lower()

            analysis = {
                'word_count': len(body.split()),
                'character_count': len(body),
                'line_count': len(body.splitlines()),
                'has_attachments': False,  # This would be set from the email message object
                'is_html': self._is_html_content(body),
                'language': self._detect_language(full_text),
                'sentiment': self._analyze_sentiment(full_text),
                'actions_required': self._identify_actions(full_text),
                'urgency_level': self._assess_urgency(full_text),
                'topics': self._extract_topics(full_text),
                'questions_asked': self._count_questions(body),
                'is_reply': self._is_reply_email(subject),
                'is_forwarded': self._is_forwarded_email(subject, body)
            }

            return analysis

        except Exception as e:
            logger.error("Error analyzing email content", error=str(e))
            raise EmailParsingError(f"Content analysis failed: {str(e)}")

    def extract_key_information(self, subject: str, body: str) -> Dict[str, Any]:
        """Extract key information and action items from email."""
        try:
            key_info = {
                'main_subject': self._extract_main_subject(subject),
                'key_points': self._extract_key_points(body),
                'action_items': self._extract_action_items(body),
                'deadlines': self._extract_deadlines(body),
                'important_dates': self._extract_important_dates(body),
                'contact_info': self._extract_contact_info(body),
                'locations': self._extract_locations(body),
                'companies': self._extract_companies(body),
                'names': self._extract_names(body)
            }

            return key_info

        except Exception as e:
            logger.error("Error extracting key information", error=str(e))
            raise EmailParsingError(f"Key information extraction failed: {str(e)}")

    def sanitize_content(self, content: str) -> str:
        """Sanitize email content for safe processing."""
        try:
            if not content:
                return ""

            # Remove HTML tags
            content = self._remove_html_tags(content)

            # Decode HTML entities
            content = html.unescape(content)

            # Remove excessive whitespace
            content = re.sub(r'\s+', ' ', content)

            # Remove potentially harmful content
            content = self._remove_suspicious_content(content)

            # Limit length for processing
            max_length = 10000
            if len(content) > max_length:
                content = content[:max_length] + "..."

            return content.strip()

        except Exception as e:
            logger.error("Error sanitizing content", error=str(e))
            return content[:1000] if content else ""

    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        return list(set(self.url_pattern.findall(text)))

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        return list(set(self.email_pattern.findall(text)))

    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        return list(set(self.phone_pattern.findall(text)))

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        return list(set(self.date_pattern.findall(text)))

    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text."""
        mention_pattern = re.compile(r'@\w+')
        return list(set(mention_pattern.findall(text)))

    def _is_html_content(self, text: str) -> bool:
        """Check if content contains HTML."""
        html_indicators = ['<html', '<div', '<p>', '<br>', '<span', '<body']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in html_indicators)

    def _detect_language(self, text: str) -> str:
        """Simple language detection."""
        # This is a very basic implementation
        # In production, use a proper language detection library
        english_indicators = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
        words = text.lower().split()

        if len(words) == 0:
            return 'unknown'

        english_word_count = sum(1 for word in words if word in english_indicators)
        english_ratio = english_word_count / len(words)

        if english_ratio > 0.1:
            return 'english'
        else:
            return 'unknown'

    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'wonderful', 'amazing', 'love', 'like', 'happy', 'pleased']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'angry', 'frustrated', 'disappointed', 'problem']

        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def _identify_actions(self, text: str) -> List[str]:
        """Identify action items in text."""
        actions = []
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in self.action_keywords):
                actions.append(sentence)

        return actions

    def _assess_urgency(self, text: str) -> str:
        """Assess urgency level of email."""
        urgency_score = 0
        text_lower = text.lower()

        for keyword in self.urgency_keywords:
            if keyword in text_lower:
                urgency_score += 1

        if urgency_score >= 3:
            return 'high'
        elif urgency_score >= 1:
            return 'medium'
        else:
            return 'low'

    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text."""
        # Simple topic extraction based on common business keywords
        topic_keywords = {
            'meeting': ['meeting', 'schedule', 'appointment', 'call', 'conference'],
            'project': ['project', 'task', 'deadline', 'milestone', 'deliverable'],
            'finance': ['payment', 'invoice', 'budget', 'cost', 'price', 'quote'],
            'support': ['help', 'support', 'issue', 'problem', 'bug', 'error'],
            'sales': ['sale', 'order', 'purchase', 'buy', 'customer', 'client'],
            'hr': ['hr', 'human resources', 'hiring', 'interview', 'employee', 'team'],
            'technical': ['technical', 'development', 'programming', 'code', 'system', 'software']
        }

        topics = []
        text_lower = text.lower()

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)

        return topics

    def _count_questions(self, text: str) -> int:
        """Count number of questions in text."""
        question_count = text.count('?')
        return question_count

    def _is_reply_email(self, subject: str) -> bool:
        """Check if this is a reply email."""
        subject_lower = subject.lower()
        return subject_lower.startswith('re:') or 're:' in subject_lower

    def _is_forwarded_email(self, subject: str, body: str) -> bool:
        """Check if this is a forwarded email."""
        subject_lower = subject.lower()
        body_lower = body.lower()
        return (
            subject_lower.startswith('fwd:') or
            'fwd:' in subject_lower or
            'forwarded message' in body_lower
        )

    def _extract_main_subject(self, subject: str) -> str:
        """Extract the main subject, removing Re: and Fwd: prefixes."""
        # Remove reply/forward prefixes
        clean_subject = re.sub(r'^(Re|Fwd):\s*', '', subject, flags=re.IGNORECASE)
        return clean_subject.strip()

    def _extract_key_points(self, body: str) -> List[str]:
        """Extract key points from email body."""
        sentences = re.split(r'[.!?]+', body)
        key_points = []

        for sentence in sentences:
            sentence = sentence.strip()
            # Consider sentences with 10-50 words as potential key points
            word_count = len(sentence.split())
            if 10 <= word_count <= 50 and sentence:
                key_points.append(sentence)

        return key_points[:5]  # Return top 5 key points

    def _extract_action_items(self, body: str) -> List[str]:
        """Extract action items from email body."""
        return self._identify_actions(body)

    def _extract_deadlines(self, body: str) -> List[str]:
        """Extract deadlines from email body."""
        deadline_patterns = [
            r'deadline:\s*(.+)',
            r'due\s+(by|on)\s*(.+)',
            r'complete\s+by\s*(.+)',
            r'finish\s+by\s*(.+)'
        ]

        deadlines = []
        for pattern in deadline_patterns:
            matches = re.findall(pattern, body, flags=re.IGNORECASE)
            deadlines.extend(matches)

        return list(set(deadlines))

    def _extract_important_dates(self, body: str) -> List[str]:
        """Extract important dates from email body."""
        return self._extract_dates(body)

    def _extract_contact_info(self, body: str) -> Dict[str, List[str]]:
        """Extract contact information from email body."""
        return {
            'emails': self._extract_emails(body),
            'phone_numbers': self._extract_phone_numbers(body)
        }

    def _extract_locations(self, body: str) -> List[str]:
        """Extract location mentions (simple implementation)."""
        # This is a basic implementation
        location_keywords = ['office', 'meeting room', 'conference room', 'building', 'address']
        locations = []

        sentences = re.split(r'[.!?]+', body)
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in location_keywords):
                locations.append(sentence.strip())

        return locations

    def _extract_companies(self, body: str) -> List[str]:
        """Extract company mentions (simple implementation)."""
        # Basic pattern matching for capitalized words that might be company names
        company_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Ltd|Co))?\b')
        return list(set(company_pattern.findall(body)))

    def _extract_names(self, body: str) -> List[str]:
        """Extract person names (simple implementation)."""
        # Basic pattern for capitalized words that might be names
        name_pattern = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b')
        return list(set(name_pattern.findall(body)))

    def _remove_html_tags(self, text: str) -> str:
        """Remove HTML tags from text."""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

    def _remove_suspicious_content(self, text: str) -> str:
        """Remove potentially suspicious or harmful content."""
        # Remove script tags and javascript
        text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

        # Remove potentially dangerous URLs
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)

        # Remove excessive special characters that might indicate attacks
        text = re.sub(r'[<>]{3,}', '', text)

        return text