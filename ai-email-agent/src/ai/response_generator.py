import asyncio
import re
from typing import Dict, Any, Optional, Tuple
from email.utils import parseaddr

from .ollama_client import OllamaClient
from .prompt_templates import EmailPromptTemplates, EmailType, ResponseStyleGuide
from ..config.settings import get_settings
from ..utils.logger import get_logger
from ..utils.exceptions import AIServiceError, AIResponseError, SecurityError, ContentFilterError

logger = get_logger(__name__)
settings = get_settings()


class EmailResponseGenerator:
    """Generates AI-powered email responses."""

    def __init__(self, ollama_client: OllamaClient = None):
        """Initialize the response generator."""
        self.ollama_client = ollama_client or OllamaClient()
        self.content_filter = ContentFilter()

    async def generate_response(
        self,
        sender_email: str,
        sender_name: str = None,
        subject: str = None,
        email_body: str = None,
        additional_context: Optional[Dict[str, Any]] = None,
        preferred_style: str = "business"
    ) -> str:
        """Generate an appropriate email response."""
        try:
            logger.info(
                "Generating email response",
                sender=sender_email,
                subject=subject,
                style=preferred_style
            )

            # Security checks
            await self._validate_request(sender_email, email_body)

            # Clean and prepare input
            cleaned_body = self._clean_email_body(email_body or "")
            sender_name = sender_name or self._extract_name_from_email(sender_email)

            # Determine email type
            email_type = await self._classify_email_type(
                sender_email, subject, cleaned_body
            )

            # Check if we should respond to this email
            if not await self._should_respond(email_type, sender_email, cleaned_body):
                logger.info("Email flagged for no-response", sender=sender_email, email_type=email_type.value)
                return None

            # Build prompts using appropriate template
            system_prompt, user_prompt = EmailPromptTemplates.build_prompt(
                email_type=email_type,
                sender_name=sender_name,
                sender_email=sender_email,
                subject=subject or "No subject",
                email_body=cleaned_body,
                additional_context=additional_context
            )

            # Add style guidelines to system prompt
            style_guidelines = self._get_style_guidelines(preferred_style)
            system_prompt += f"\n\n{style_guidelines}"

            # Generate response using Ollama
            async with self.ollama_client:
                response = await self.ollama_client.generate_response(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=settings.ai.temperature,
                    max_tokens=settings.ai.max_tokens
                )

            # Clean and validate the generated response
            cleaned_response = self._clean_response(response.response)

            # Final content filter check
            if not self.content_filter.is_safe_content(cleaned_response):
                raise ContentFilterError("Generated response failed content safety check")

            logger.info(
                "Email response generated successfully",
                sender=sender_email,
                response_length=len(cleaned_response),
                email_type=email_type.value
            )

            return cleaned_response

        except Exception as e:
            logger.error("Failed to generate email response", sender=sender_email, error=str(e))
            raise AIResponseError(f"Response generation failed: {str(e)}")

    async def _classify_email_type(
        self,
        sender_email: str,
        subject: str,
        body: str
    ) -> EmailType:
        """Classify the type of email for appropriate response handling."""
        try:
            # Simple keyword-based classification
            text_to_analyze = f"{subject or ''} {body or ''}".lower()

            # Check for spam indicators
            spam_indicators = [
                'unsubscribe', 'click here', 'limited time', 'act now',
                'congratulations', 'winner', 'free money', 'guarantee'
            ]
            if any(indicator in text_to_analyze for indicator in spam_indicators):
                return EmailType.SPAM

            # Check for meeting requests
            meeting_keywords = ['meeting', 'schedule', 'appointment', 'call', 'discuss']
            if any(keyword in text_to_analyze for keyword in meeting_keywords):
                return EmailType.MEETING_REQUEST

            # Check for support requests
            support_keywords = ['help', 'issue', 'problem', 'support', 'broken', 'error']
            if any(keyword in text_to_analyze for keyword in support_keywords):
                return EmailType.SUPPORT_REQUEST

            # Check for job applications
            job_keywords = ['application', 'resume', 'cv', 'position', 'hiring', 'interview']
            if any(keyword in text_to_analyze for keyword in job_keywords):
                return EmailType.JOB_APPLICATION

            # Check for business inquiries
            business_keywords = ['inquiry', 'proposal', 'business', 'service', 'price', 'quote']
            if any(keyword in text_to_analyze for keyword in business_keywords):
                return EmailType.BUSINESS_INQUIRY

            # Check for personal messages (based on sender domain familiarity)
            personal_domains = ['gmail.com', 'yahoo.com', 'outlook.com']
            if any(domain in sender_email.lower() for domain in personal_domains):
                return EmailType.PERSONAL_MESSAGE

            return EmailType.UNCLEAR

        except Exception as e:
            logger.warning("Failed to classify email type", error=str(e))
            return EmailType.UNCLEAR

    async def _should_respond(
        self,
        email_type: EmailType,
        sender_email: str,
        body: str
    ) -> bool:
        """Determine if we should generate a response for this email."""
        # Don't respond to spam
        if email_type == EmailType.SPAM:
            return False

        # Don't respond to mass emails/newsletters
        if self._is_mass_email(sender_email, body):
            return False

        # Check sender whitelist/blacklist
        if settings.processing.allowed_senders and sender_email not in settings.processing.allowed_senders:
            return False

        if settings.processing.blocked_senders and sender_email in settings.processing.blocked_senders:
            return False

        # Don't respond during quiet hours unless urgent
        if self._is_quiet_hours() and not await self._is_urgent_email(email_type, body):
            return False

        return True

    def _clean_email_body(self, body: str) -> str:
        """Clean and normalize email body content."""
        if not body:
            return ""

        # Remove excessive whitespace
        body = re.sub(r'\s+', ' ', body)

        # Remove forwarded email markers
        body = re.sub(r'>+', '', body)

        # Remove email signatures (simple heuristic)
        lines = body.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip common signature indicators
            if any(marker in line.lower() for marker in ['--', 'sent from', 'regards', 'sincerely']):
                break
            if line:
                cleaned_lines.append(line)

        return ' '.join(cleaned_lines)

    def _clean_response(self, response: str) -> str:
        """Clean and format the AI-generated response."""
        if not response:
            return ""

        # Remove excessive whitespace
        response = re.sub(r'\s+', ' ', response)

        # Remove any template markers or instructions
        response = re.sub(r'Response:', '', response, flags=re.IGNORECASE)

        # Ensure proper formatting
        response = response.strip()

        # Add appropriate signature if not present
        if not any(marker in response.lower() for marker in ['thanks', 'regards', 'sincerely']):
            response += "\n\nBest regards"

        return response

    def _extract_name_from_email(self, email: str) -> str:
        """Extract name from email address."""
        name, email_addr = parseaddr(email)
        return name if name else email_addr.split('@')[0].title()

    def _get_style_guidelines(self, style: str) -> str:
        """Get style guidelines based on preferred style."""
        style_guides = {
            "formal": ResponseStyleGuide.get_formal_style_guidelines(),
            "casual": ResponseStyleGuide.get_casual_style_guidelines(),
            "business": ResponseStyleGuide.get_business_style_guidelines()
        }
        return style_guides.get(style, ResponseStyleGuide.get_business_style_guidelines())

    def _is_mass_email(self, sender_email: str, body: str) -> bool:
        """Check if this appears to be a mass email."""
        # Check for common mass email indicators
        mass_indicators = [
            'unsubscribe', 'newsletter', 'promotional', 'marketing',
            'bulk', 'campaign', 'list serve'
        ]

        text_to_check = f"{sender_email} {body or ''}".lower()
        return any(indicator in text_to_check for indicator in mass_indicators)

    def _is_quiet_hours(self) -> bool:
        """Check if current time is during quiet hours."""
        from datetime import datetime, time

        now = datetime.now().time()
        quiet_start = time.fromisoformat(settings.processing.quiet_hours_start)
        quiet_end = time.fromisoformat(settings.processing.quiet_hours_end)

        if quiet_start <= quiet_end:
            # Simple case: quiet hours don't cross midnight
            return quiet_start <= now <= quiet_end
        else:
            # Quiet hours cross midnight (e.g., 22:00 to 08:00)
            return now >= quiet_start or now <= quiet_end

    async def _is_urgent_email(self, email_type: EmailType, body: str) -> bool:
        """Check if email appears to be urgent."""
        urgent_keywords = ['urgent', 'asap', 'emergency', 'immediately', 'critical']
        return any(keyword in body.lower() for keyword in urgent_keywords)

    async def _validate_request(self, sender_email: str, body: str) -> None:
        """Validate the email request for security and content safety."""
        # Basic email format validation
        if not sender_email or '@' not in sender_email:
            raise SecurityError("Invalid sender email address")

        # Content length check
        if body and len(body) > 10000:  # 10k character limit
            raise SecurityError("Email content too long")

        # Content safety check
        if body and not self.content_filter.is_safe_content(body):
            raise ContentFilterError("Email content failed safety check")


class ContentFilter:
    """Content filtering for security and appropriateness."""

    def __init__(self):
        """Initialize content filter."""
        # Simple keyword-based filtering
        self.blocked_keywords = [
            # Explicit content
            'explicit', 'adult', 'nsfw',
            # Harmful content
            'harmful', 'dangerous', 'illegal',
            # Personal information requests
            'ssn', 'social security', 'credit card', 'password',
            # Spam indicators
            'click here', 'act now', 'limited offer'
        ]

    def is_safe_content(self, content: str) -> bool:
        """Check if content is safe for processing."""
        if not content:
            return True

        content_lower = content.lower()

        # Check for blocked keywords
        for keyword in self.blocked_keywords:
            if keyword in content_lower:
                logger.warning("Blocked keyword found in content", keyword=keyword)
                return False

        # Additional safety checks can be added here
        return True