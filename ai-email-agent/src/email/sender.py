import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta

from ..config.settings import get_settings
from ..utils.logger import get_logger, audit_logger
from ..utils.exceptions import EmailSendingError, EmailAuthenticationError

logger = get_logger(__name__)
settings = get_settings()


class EmailSender:
    """Handles sending emails via Gmail SMTP."""

    def __init__(self):
        """Initialize email sender."""
        self.smtp = None
        self.email_address = settings.email.gmail_username
        self.app_password = settings.email.gmail_app_password
        self.smtp_server = settings.email.smtp_server
        self.smtp_port = settings.email.smtp_port
        self.use_tls = settings.email.use_tls
        self._rate_limit_tracker = {}

    async def connect(self) -> bool:
        """Connect to Gmail SMTP server."""
        try:
            logger.info("Connecting to Gmail SMTP server", server=self.smtp_server)

            # Create SSL context
            context = ssl.create_default_context()

            # Create SMTP connection
            self.smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.use_tls:
                # Start TLS encryption
                self.smtp.starttls(context=context)

            # Login with app password
            try:
                self.smtp.login(self.email_address, self.app_password)
                logger.info("Successfully authenticated with Gmail SMTP")
                return True

            except smtplib.SMTPAuthenticationError as e:
                logger.error("Gmail SMTP authentication failed", error=str(e))
                raise EmailAuthenticationError("Invalid SMTP credentials")

        except Exception as e:
            logger.error("Failed to connect to Gmail SMTP", error=str(e))
            raise EmailSendingError(f"SMTP connection failed: {str(e)}")

    async def disconnect(self):
        """Disconnect from SMTP server."""
        try:
            if self.smtp:
                self.smtp.quit()
                self.smtp = None
                logger.info("Disconnected from Gmail SMTP server")
        except Exception as e:
            logger.warning("Error during SMTP disconnection", error=str(e))

    async def send_reply(
        self,
        to_email: str,
        subject: str,
        body: str,
        original_message_id: str = None,
        original_sender: str = None,
        original_subject: str = None,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """Send a reply email."""
        try:
            # Check rate limiting
            if not await self._check_rate_limit(to_email):
                logger.warning("Rate limit exceeded for recipient", recipient=to_email)
                raise EmailSendingError("Rate limit exceeded")

            await self._ensure_connection()

            # Create message
            message = MIMEMultipart()
            message["From"] = formataddr(("AI Email Agent", self.email_address))
            message["To"] = to_email
            message["Subject"] = self._format_reply_subject(original_subject or subject)

            # Add reply headers if replying to original message
            if original_message_id:
                message["In-Reply-To"] = original_message_id
                message["References"] = original_message_id

            # Add CC recipients
            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)

            # Create reply body with proper formatting
            reply_body = self._format_reply_body(
                body=body,
                original_sender=original_sender,
                original_subject=original_subject
            )

            # Add the text body
            message.attach(MIMEText(reply_body, "plain", "utf-8"))

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    await self._add_attachment(message, attachment)

            # Prepare all recipients
            all_recipients = [to_email]
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)

            # Send the email
            try:
                text = message.as_string()
                self.smtp.sendmail(self.email_address, all_recipients, text)

                logger.info(
                    "Reply sent successfully",
                    to=to_email,
                    subject=message["Subject"],
                    recipients_count=len(all_recipients)
                )

                # Log the send action
                audit_logger.log_email_sent(
                    recipient=to_email,
                    subject=message["Subject"],
                    success=True
                )

                return True

            except smtplib.SMTPRecipientsRefused:
                error_msg = f"All recipients refused: {to_email}"
                logger.error("SMTP recipients refused", recipients=to_email)
                raise EmailSendingError(error_msg)

            except smtplib.SMTPSenderRefused:
                logger.error("SMTP sender refused", sender=self.email_address)
                raise EmailAuthenticationError("Sender address refused")

            except smtplib.SMTPException as e:
                logger.error("SMTP error occurred", error=str(e))
                raise EmailSendingError(f"SMTP error: {str(e)}")

        except Exception as e:
            logger.error("Failed to send reply email", to=to_email, error=str(e))
            audit_logger.log_email_sent(
                recipient=to_email,
                subject=subject,
                success=False
            )
            raise EmailSendingError(f"Failed to send email: {str(e)}")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_name: str = "AI Email Agent",
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """Send a new email (not a reply)."""
        try:
            # Check rate limiting
            if not await self._check_rate_limit(to_email):
                logger.warning("Rate limit exceeded for recipient", recipient=to_email)
                raise EmailSendingError("Rate limit exceeded")

            await self._ensure_connection()

            # Create message
            message = MIMEMultipart()
            message["From"] = formataddr((from_name, self.email_address))
            message["To"] = to_email
            message["Subject"] = subject

            # Add CC recipients
            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)

            # Add the text body with signature
            signed_body = self._add_signature(body)
            message.attach(MIMEText(signed_body, "plain", "utf-8"))

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    await self._add_attachment(message, attachment)

            # Prepare all recipients
            all_recipients = [to_email]
            if cc_emails:
                all_recipients.extend(cc_emails)
            if bcc_emails:
                all_recipients.extend(bcc_emails)

            # Send the email
            try:
                text = message.as_string()
                self.smtp.sendmail(self.email_address, all_recipients, text)

                logger.info(
                    "Email sent successfully",
                    to=to_email,
                    subject=subject,
                    recipients_count=len(all_recipients)
                )

                # Log the send action
                audit_logger.log_email_sent(
                    recipient=to_email,
                    subject=subject,
                    success=True
                )

                return True

            except smtplib.SMTPRecipientsRefused:
                error_msg = f"All recipients refused: {to_email}"
                logger.error("SMTP recipients refused", recipients=to_email)
                raise EmailSendingError(error_msg)

            except smtplib.SMTPException as e:
                logger.error("SMTP error occurred", error=str(e))
                raise EmailSendingError(f"SMTP error: {str(e)}")

        except Exception as e:
            logger.error("Failed to send email", to=to_email, error=str(e))
            audit_logger.log_email_sent(
                recipient=to_email,
                subject=subject,
                success=False
            )
            raise EmailSendingError(f"Failed to send email: {str(e)}")

    def _format_reply_subject(self, original_subject: str) -> str:
        """Format reply subject with Re: prefix."""
        if original_subject.lower().startswith("re:"):
            return original_subject
        return f"Re: {original_subject}"

    def _format_reply_body(
        self,
        body: str,
        original_sender: str = None,
        original_subject: str = None
    ) -> str:
        """Format the reply body with proper structure."""
        reply_lines = []

        # Add the main reply content
        reply_lines.append(body.strip())
        reply_lines.append("")

        # Add signature
        reply_lines.append("")
        reply_lines.append("--")
        reply_lines.append("AI Email Agent")
        reply_lines.append("This response was generated automatically by an AI assistant.")

        # Add reference to original message
        if original_sender and original_subject:
            reply_lines.append("")
            reply_lines.append(f"On {datetime.now().strftime('%Y-%m-%d %H:%M')}, {original_sender} wrote:")
            reply_lines.append(f"Subject: {original_subject}")

        return "\n".join(reply_lines)

    def _add_signature(self, body: str) -> str:
        """Add signature to email body."""
        signature = "\n\n--\nAI Email Agent\nThis message was sent automatically by an AI email assistant."

        if body.strip().endswith(signature):
            return body

        return f"{body.rstrip()}{signature}"

    async def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message."""
        try:
            # Extract attachment details
            filename = attachment.get("filename", "attachment")
            content_type = attachment.get("content_type", "application/octet-stream")
            content = attachment.get("content", "")

            # Create MIMEBase object
            part = MIMEBase(content_type.split('/')[0], content_type.split('/')[1])
            part.set_payload(content)

            # Encode the attachment
            encoders.encode_base64(part)

            # Add headers
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}"
            )

            # Attach to message
            message.attach(part)

            logger.info("Attachment added to email", filename=filename, size=len(content))

        except Exception as e:
            logger.error("Error adding attachment", filename=attachment.get("filename"), error=str(e))
            # Continue without attachment rather than failing the entire email

    async def _check_rate_limit(self, recipient: str) -> bool:
        """Check if rate limit is exceeded for a recipient."""
        try:
            current_time = datetime.now()
            rate_limit_window = 300  # 5 minutes
            max_emails_per_window = 5  # Max 5 emails per 5 minutes per recipient

            # Clean old entries
            cutoff_time = current_time - timedelta(seconds=rate_limit_window)
            if recipient in self._rate_limit_tracker:
                self._rate_limit_tracker[recipient] = [
                    timestamp for timestamp in self._rate_limit_tracker[recipient]
                    if timestamp > cutoff_time
                ]

            # Check current count
            if recipient not in self._rate_limit_tracker:
                self._rate_limit_tracker[recipient] = []

            if len(self._rate_limit_tracker[recipient]) >= max_emails_per_window:
                return False

            # Add current timestamp
            self._rate_limit_tracker[recipient].append(current_time)
            return True

        except Exception as e:
            logger.error("Error checking rate limit", recipient=recipient, error=str(e))
            return True  # Allow sending if rate limit check fails

    async def _ensure_connection(self):
        """Ensure SMTP connection is active."""
        try:
            if not self.smtp:
                await self.connect()
                return

            # Test connection with NOOP
            self.smtp.noop()

        except Exception:
            # Connection lost, try to reconnect
            logger.info("SMTP connection lost, attempting to reconnect")
            await self.connect()

    async def test_connection(self) -> Dict[str, Any]:
        """Test SMTP connection and authentication."""
        try:
            await self.connect()

            # Send test NOOP to verify connection
            self.smtp.noop()

            return {
                "connected": True,
                "authenticated": True,
                "server": self.smtp_server,
                "email": self.email_address,
                "port": self.smtp_port,
                "use_tls": self.use_tls
            }

        except EmailAuthenticationError:
            return {
                "connected": True,
                "authenticated": False,
                "server": self.smtp_server,
                "email": self.email_address,
                "error": "Authentication failed"
            }

        except Exception as e:
            return {
                "connected": False,
                "authenticated": False,
                "server": self.smtp_server,
                "email": self.email_address,
                "error": str(e)
            }

    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        try:
            if not self.smtp:
                return {"connected": False, "authenticated": False}

            # Test connection with NOOP
            self.smtp.noop()

            return {
                "connected": True,
                "authenticated": True,
                "server": self.smtp_server,
                "email": self.email_address
            }

        except Exception:
            return {"connected": False, "authenticated": False}