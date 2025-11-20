import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from .reader import EmailReader, EmailMessage
from .sender import EmailSender
from .parser import EmailParser
from ..ai.response_generator import EmailResponseGenerator
from ..ai.ollama_client import OllamaClient
from ..config.settings import get_settings
from ..utils.logger import get_logger, audit_logger
from ..utils.exceptions import (
    EmailAgentException,
    ProcessingError,
    AIServiceError,
    SecurityError,
    ContentFilterError
)

logger = get_logger(__name__)
settings = get_settings()


class EmailProcessor:
    """Main email processing engine."""

    def __init__(self):
        """Initialize the email processor."""
        self.reader = EmailReader()
        self.sender = EmailSender()
        self.parser = EmailParser()
        self.ollama_client = OllamaClient()
        self.response_generator = EmailResponseGenerator(self.ollama_client)
        self.processing_stats = {
            'total_processed': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'skipped_emails': 0,
            'errors': 0
        }

    async def initialize(self) -> bool:
        """Initialize all components and test connections."""
        try:
            logger.info("Initializing email processor")

            # Test Ollama connection
            ollama_connected = await self.ollama_client.check_connection()
            if not ollama_connected:
                logger.error("Failed to connect to Ollama service")
                raise AIServiceError("Ollama service not available")

            # Test email connections
            reader_status = await self.reader.get_connection_status()
            if not reader_status.get('connected'):
                await self.reader.connect()

            sender_status = await self.sender.test_connection()
            if not sender_status.get('connected'):
                logger.error("Failed to connect to email sender")
                raise EmailAgentException("Email sender connection failed")

            logger.info("Email processor initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize email processor", error=str(e))
            return False

    async def process_emails(
        self,
        limit: int = None,
        sender_filter: str = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Process unread emails."""
        try:
            logger.info("Starting email processing", limit=limit, dry_run=dry_run)

            # Ensure connections are active
            await self._ensure_connections()

            # Fetch unread emails
            emails = await self.reader.get_unread_emails(
                limit=limit,
                sender_filter=sender_filter
            )

            if not emails:
                logger.info("No unread emails to process")
                return {
                    'processed': 0,
                    'responded': 0,
                    'skipped': 0,
                    'errors': 0,
                    'processing_time': 0
                }

            start_time = datetime.now()
            processing_results = []

            # Process each email
            for email in emails:
                try:
                    result = await self._process_single_email(email, dry_run)
                    processing_results.append(result)

                    # Update statistics
                    self.processing_stats['total_processed'] += 1

                    if result['responded']:
                        self.processing_stats['successful_responses'] += 1
                    elif result['skipped']:
                        self.processing_stats['skipped_emails'] += 1
                    else:
                        self.processing_stats['failed_responses'] += 1

                except Exception as e:
                    logger.error("Error processing email", email_id=email.message_id, error=str(e))
                    self.processing_stats['errors'] += 1
                    processing_results.append({
                        'email_id': email.message_id,
                        'sender': email.sender,
                        'subject': email.subject,
                        'responded': False,
                        'skipped': False,
                        'error': str(e)
                    })

            processing_time = (datetime.now() - start_time).total_seconds()

            # Calculate results
            responded_count = sum(1 for r in processing_results if r['responded'])
            skipped_count = sum(1 for r in processing_results if r['skipped'])
            error_count = sum(1 for r in processing_results if r.get('error'))

            logger.info(
                "Email processing completed",
                total=len(emails),
                responded=responded_count,
                skipped=skipped_count,
                errors=error_count,
                processing_time=processing_time
            )

            return {
                'processed': len(emails),
                'responded': responded_count,
                'skipped': skipped_count,
                'errors': error_count,
                'processing_time': processing_time,
                'results': processing_results
            }

        except Exception as e:
            logger.error("Email processing failed", error=str(e))
            raise ProcessingError(f"Processing failed: {str(e)}")

    async def _process_single_email(self, email: EmailMessage, dry_run: bool = False) -> Dict[str, Any]:
        """Process a single email message."""
        try:
            logger.info(
                "Processing email",
                sender=email.sender,
                subject=email.subject,
                message_id=email.message_id
            )

            # Security and content validation
            await self._validate_email(email)

            # Parse and analyze email content
            parsed_content = self.parser.sanitize_content(email.body)
            content_analysis = self.parser.analyze_content(email.subject, parsed_content)

            logger.info(
                "Email analyzed",
                sender=email.sender,
                word_count=content_analysis.get('word_count', 0),
                urgency=content_analysis.get('urgency_level', 'unknown')
            )

            # Determine if we should respond
            should_respond = await self._should_respond_to_email(email, content_analysis)

            if not should_respond:
                logger.info("Email flagged for no response", sender=email.sender)
                await self._handle_no_response_email(email)
                return {
                    'email_id': email.message_id,
                    'sender': email.sender,
                    'subject': email.subject,
                    'responded': False,
                    'skipped': True,
                    'reason': 'filtered_no_response'
                }

            # Generate AI response
            try:
                ai_response = await self.response_generator.generate_response(
                    sender_email=email.sender,
                    sender_name=email.sender_name,
                    subject=email.subject,
                    email_body=parsed_content,
                    additional_context={
                        'urgency': content_analysis.get('urgency_level'),
                        'topics': content_analysis.get('topics', []),
                        'actions_required': content_analysis.get('actions_required', [])
                    },
                    preferred_style=self._determine_response_style(content_analysis)
                )

                if not ai_response:
                    logger.info("AI response generation returned empty response")
                    await self._handle_no_response_email(email)
                    return {
                        'email_id': email.message_id,
                        'sender': email.sender,
                        'subject': email.subject,
                        'responded': False,
                        'skipped': True,
                        'reason': 'no_ai_response'
                    }

                logger.info("AI response generated", response_length=len(ai_response))

            except (AIServiceError, ContentFilterError) as e:
                logger.error("AI response generation failed", error=str(e))
                ai_response = await self._generate_fallback_response(email, content_analysis)

            # Send response (unless dry run)
            response_sent = False
            if not dry_run:
                try:
                    response_sent = await self.sender.send_reply(
                        to_email=email.sender,
                        subject=email.subject,
                        body=ai_response,
                        original_message_id=email.message_id,
                        original_sender=email.sender,
                        original_subject=email.subject
                    )

                    if response_sent:
                        logger.info("Response sent successfully", recipient=email.sender)

                except Exception as e:
                    logger.error("Failed to send response", error=str(e))
                    response_sent = False

            # Handle post-processing (mark as read, delete, etc.)
            if not dry_run and response_sent:
                await self._handle_processed_email(email)

            return {
                'email_id': email.message_id,
                'sender': email.sender,
                'subject': email.subject,
                'responded': response_sent,
                'skipped': False,
                'response_length': len(ai_response) if ai_response else 0,
                'dry_run': dry_run
            }

        except SecurityError as e:
            logger.warning("Email failed security validation", sender=email.sender, error=str(e))
            return {
                'email_id': email.message_id,
                'sender': email.sender,
                'subject': email.subject,
                'responded': False,
                'skipped': True,
                'reason': 'security_error',
                'error': str(e)
            }

        except Exception as e:
            logger.error("Unexpected error processing email", sender=email.sender, error=str(e))
            return {
                'email_id': email.message_id,
                'sender': email.sender,
                'subject': email.subject,
                'responded': False,
                'skipped': False,
                'error': str(e)
            }

    async def _validate_email(self, email: EmailMessage):
        """Validate email for security and processing suitability."""
        # Check sender against whitelist/blacklist
        if settings.processing.allowed_senders:
            if email.sender not in settings.processing.allowed_senders:
                raise SecurityError(f"Sender not in allowed list: {email.sender}")

        if settings.processing.blocked_senders:
            if email.sender in settings.processing.blocked_senders:
                raise SecurityError(f"Sender blocked: {email.sender}")

        # Check content safety
        if settings.security.enable_content_filter:
            content = f"{email.subject} {email.body}"
            if len(content) > 50000:  # 50k character limit
                raise SecurityError("Email content too large")

            # Additional content filtering can be added here

        # Check attachment size
        total_attachment_size = sum(att.get('size', 0) for att in email.attachments)
        max_size_bytes = settings.security.max_attachment_size_mb * 1024 * 1024
        if total_attachment_size > max_size_bytes:
            raise SecurityError(f"Attachments too large: {total_attachment_size} bytes")

    async def _should_respond_to_email(self, email: EmailMessage, analysis: Dict[str, Any]) -> bool:
        """Determine if we should respond to this email."""
        # Don't respond to mass emails
        if analysis.get('is_reply', False) and self._is_mass_reply(email):
            return False

        # Don't respond during quiet hours unless urgent
        if self._is_quiet_hours() and analysis.get('urgency_level') != 'high':
            return False

        # Check if email has meaningful content
        if analysis.get('word_count', 0) < 3:
            return False

        # Don't respond to auto-generated emails
        subject_lower = email.subject.lower()
        auto_indicators = ['auto-reply', 'automatic', 'out of office', 'vacation', 'away']
        if any(indicator in subject_lower for indicator in auto_indicators):
            return False

        return True

    async def _generate_fallback_response(self, email: EmailMessage, analysis: Dict[str, Any]) -> str:
        """Generate a fallback response when AI fails."""
        fallback_templates = {
            'high': "Thank you for your email. I've received your urgent message and will get back to you as soon as possible.",
            'medium': "Thank you for your email. I've received your message and will respond within 24 hours.",
            'low': "Thank you for your email. I've received your message and will respond when able."
        }

        urgency = analysis.get('urgency_level', 'medium')
        response = fallback_templates.get(urgency, fallback_templates['medium'])

        logger.info("Using fallback response", urgency=urgency, sender=email.sender)
        return response

    def _determine_response_style(self, analysis: Dict[str, Any]) -> str:
        """Determine appropriate response style based on email analysis."""
        # Simple logic for style determination
        if analysis.get('urgency_level') == 'high':
            return 'business'  # Professional but direct
        elif 'personal' in analysis.get('topics', []):
            return 'casual'
        else:
            return 'business'

    async def _handle_processed_email(self, email: EmailMessage):
        """Handle email after successful processing."""
        try:
            # Mark as read
            await self.reader.mark_as_read(email)

            # Delete if configured
            if settings.processing.delete_processed:
                await self.reader.delete_email(email)
                logger.info("Email deleted after processing", message_id=email.message_id)

            audit_logger.log_email_processed(
                sender=email.sender,
                subject=email.subject,
                action="processed_and_responded"
            )

        except Exception as e:
            logger.error("Error handling processed email", error=str(e))

    async def _handle_no_response_email(self, email: EmailMessage):
        """Handle email that doesn't require response."""
        try:
            # Mark as read but don't delete
            await self.reader.mark_as_read(email)

            audit_logger.log_email_processed(
                sender=email.sender,
                subject=email.subject,
                action="marked_read_no_response"
            )

        except Exception as e:
            logger.error("Error handling no-response email", error=str(e))

    async def _ensure_connections(self):
        """Ensure all connections are active."""
        try:
            # Check reader connection
            reader_status = await self.reader.get_connection_status()
            if not reader_status.get('connected'):
                await self.reader.connect()

            # Check sender connection
            sender_status = await self.sender.get_connection_status()
            if not sender_status.get('connected'):
                await self.sender.connect()

        except Exception as e:
            logger.error("Error ensuring connections", error=str(e))
            raise EmailAgentException("Connection check failed")

    def _is_mass_reply(self, email: EmailMessage) -> bool:
        """Check if this appears to be a mass reply email."""
        # Simple heuristics for detecting mass replies
        indicators = ['all', 'everyone', 'team', 'undisclosed-recipients']
        subject_lower = email.subject.lower()
        return any(indicator in subject_lower for indicator in indicators)

    def _is_quiet_hours(self) -> bool:
        """Check if current time is during quiet hours."""
        from datetime import time

        now = datetime.now().time()
        quiet_start = time.fromisoformat(settings.processing.quiet_hours_start)
        quiet_end = time.fromisoformat(settings.processing.quiet_hours_end)

        if quiet_start <= quiet_end:
            return quiet_start <= now <= quiet_end
        else:
            return now >= quiet_start or now <= quiet_end

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return self.processing_stats.copy()

    async def reset_stats(self):
        """Reset processing statistics."""
        self.processing_stats = {
            'total_processed': 0,
            'successful_responses': 0,
            'failed_responses': 0,
            'skipped_emails': 0,
            'errors': 0
        }
        logger.info("Processing statistics reset")

    async def cleanup(self):
        """Clean up resources."""
        try:
            await self.reader.disconnect()
            await self.sender.disconnect()
            await self.ollama_client.__aexit__(None, None, None)
            logger.info("Email processor cleanup completed")
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))