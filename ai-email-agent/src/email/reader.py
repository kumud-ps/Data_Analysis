import asyncio
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import ssl

from ..config.settings import get_settings
from ..utils.logger import get_logger, audit_logger
from ..utils.exceptions import EmailConnectionError, EmailAuthenticationError, EmailParsingError

logger = get_logger(__name__)
settings = get_settings()


class EmailMessage:
    """Represents an email message."""

    def __init__(
        self,
        message_id: str,
        sender: str,
        sender_name: str,
        subject: str,
        body: str,
        html_body: str = None,
        date: datetime = None,
        attachments: List[Dict] = None,
        message_uid: str = None,
        flags: List[str] = None
    ):
        self.message_id = message_id
        self.sender = sender
        self.sender_name = sender_name
        self.subject = subject
        self.body = body
        self.html_body = html_body
        self.date = date or datetime.now()
        self.attachments = attachments or []
        self.message_uid = message_uid
        self.flags = flags or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "sender_name": self.sender_name,
            "subject": self.subject,
            "body": self.body,
            "html_body": self.html_body,
            "date": self.date.isoformat() if self.date else None,
            "attachments": self.attachments,
            "message_uid": self.message_uid,
            "flags": self.flags
        }


class EmailReader:
    """Handles reading emails from Gmail via IMAP."""

    def __init__(self):
        """Initialize email reader."""
        self.imap = None
        self.email_address = settings.email.gmail_username
        self.app_password = settings.email.gmail_app_password
        self.imap_server = settings.email.imap_server
        self.imap_port = settings.email.imap_port

    async def connect(self) -> bool:
        """Connect to Gmail IMAP server."""
        try:
            logger.info("Connecting to Gmail IMAP server", server=self.imap_server)

            # Create SSL context for secure connection
            context = ssl.create_default_context()

            # Connect to IMAP server
            self.imap = imaplib.IMAP4_SSL(
                host=self.imap_server,
                port=self.imap_port,
                ssl_context=context
            )

            # Login with app password
            try:
                self.imap.login(self.email_address, self.app_password)
                logger.info("Successfully authenticated with Gmail")
                return True

            except imaplib.IMAP4.error as e:
                logger.error("Gmail authentication failed", error=str(e))
                raise EmailAuthenticationError("Invalid email credentials or app password")

        except Exception as e:
            logger.error("Failed to connect to Gmail", error=str(e))
            raise EmailConnectionError(f"Connection failed: {str(e)}")

    async def disconnect(self):
        """Disconnect from IMAP server."""
        try:
            if self.imap:
                self.imap.close()
                self.imap.logout()
                self.imap = None
                logger.info("Disconnected from Gmail IMAP server")
        except Exception as e:
            logger.warning("Error during IMAP disconnection", error=str(e))

    async def select_folder(self, folder: str = "INBOX") -> bool:
        """Select email folder."""
        try:
            if not self.imap:
                await self.connect()

            result, data = self.imap.select(folder)
            if result == 'OK':
                logger.info("Selected email folder", folder=folder)
                return True
            else:
                logger.error("Failed to select folder", folder=folder, response=data)
                return False

        except Exception as e:
            logger.error("Error selecting folder", folder=folder, error=str(e))
            return False

    async def get_unread_emails(
        self,
        limit: int = None,
        sender_filter: str = None,
        subject_filter: str = None,
        date_since: datetime = None
    ) -> List[EmailMessage]:
        """Fetch unread emails from inbox."""
        try:
            await self.select_folder("INBOX")

            # Build search criteria
            search_criteria = ["(UNSEEN)"]

            if sender_filter:
                search_criteria.append(f'(FROM "{sender_filter}")')

            if subject_filter:
                search_criteria.append(f'(SUBJECT "{subject_filter}")')

            if date_since:
                date_str = date_since.strftime("%d-%b-%Y")
                search_criteria.append(f'(SINCE {date_str})')

            search_query = " ".join(search_criteria)
            logger.info("Searching for emails", query=search_query)

            # Search for emails
            result, data = self.imap.search(None, search_query)
            if result != 'OK':
                logger.error("Email search failed", response=data)
                return []

            email_ids = data[0].split()
            logger.info("Found unread emails", count=len(email_ids))

            # Apply limit if specified
            if limit and len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Get most recent emails
                logger.info("Applied limit to email fetch", limit=limit)

            # Fetch email details
            emails = []
            for email_id in email_ids:
                try:
                    email_message = await self._fetch_email(email_id)
                    if email_message:
                        emails.append(email_message)

                except Exception as e:
                    logger.error("Error fetching email", email_id=email_id, error=str(e))
                    continue

            logger.info("Successfully fetched emails", count=len(emails))
            return emails

        except Exception as e:
            logger.error("Failed to get unread emails", error=str(e))
            raise EmailConnectionError(f"Failed to fetch emails: {str(e)}")

    async def _fetch_email(self, email_id: bytes) -> Optional[EmailMessage]:
        """Fetch and parse a single email."""
        try:
            # Fetch the email
            result, data = self.imap.fetch(email_id, "(RFC822 FLAGS)")
            if result != 'OK':
                return None

            # Parse the email
            raw_email = data[0][1]
            flags_data = data[0][0]

            # Parse flags
            flags = self._parse_flags(flags_data)

            # Parse email content
            msg = email.message_from_bytes(raw_email)

            # Extract email details
            message_id = msg.get("Message-ID", "")
            sender, sender_name = self._parse_sender(msg.get("From", ""))
            subject = self._decode_header(msg.get("Subject", ""))
            date = self._parse_date(msg.get("Date"))

            # Extract body content
            body, html_body = self._extract_body(msg)

            # Extract attachments
            attachments = self._extract_attachments(msg)

            # Create EmailMessage object
            email_message = EmailMessage(
                message_id=message_id,
                sender=sender,
                sender_name=sender_name,
                subject=subject,
                body=body,
                html_body=html_body,
                date=date,
                attachments=attachments,
                message_uid=email_id.decode('utf-8'),
                flags=flags
            )

            # Log email receipt
            audit_logger.log_email_received(sender, subject, message_id)

            return email_message

        except Exception as e:
            logger.error("Error parsing email", email_id=email_id, error=str(e))
            return None

    def _parse_flags(self, flags_data: bytes) -> List[str]:
        """Parse email flags from IMAP response."""
        try:
            flags_str = flags_data.decode('utf-8')
            # Extract flags between parentheses
            if '(' in flags_str and ')' in flags_str:
                flags_part = flags_str[flags_str.find('(')+1:flags_str.find(')')]
                return [flag.strip() for flag in flags_part.split() if flag.strip()]
            return []
        except Exception:
            return []

    def _parse_sender(self, sender_header: str) -> Tuple[str, str]:
        """Parse sender email and name from header."""
        try:
            import email.utils
            parsed = email.utils.parseaddr(sender_header)
            return parsed[1], parsed[0]  # email, name
        except Exception:
            return sender_header, ""

    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += part
            return decoded_string
        except Exception:
            return header

    def _parse_date(self, date_header: str) -> datetime:
        """Parse email date."""
        try:
            import email.utils
            timestamp = email.utils.parsedate_tz(date_header)
            if timestamp:
                return datetime.fromtimestamp(email.utils.mktime_tz(timestamp))
            return datetime.now()
        except Exception:
            return datetime.now()

    def _extract_body(self, msg) -> Tuple[str, str]:
        """Extract plain text and HTML body from email message."""
        body = ""
        html_body = ""

        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue

                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')

                    elif content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        html_body = payload.decode(charset, errors='ignore')
            else:
                # Not multipart
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'

                if payload:
                    decoded = payload.decode(charset, errors='ignore')
                    if content_type == "text/plain":
                        body = decoded
                    elif content_type == "text/html":
                        html_body = decoded

        except Exception as e:
            logger.error("Error extracting email body", error=str(e))

        return body, html_body

    def _extract_attachments(self, msg) -> List[Dict[str, Any]]:
        """Extract attachment information from email message."""
        attachments = []

        try:
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition"))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        attachment_info = {
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True) or b"")
                        }
                        attachments.append(attachment_info)

        except Exception as e:
            logger.error("Error extracting attachments", error=str(e))

        return attachments

    async def mark_as_read(self, email_message: EmailMessage) -> bool:
        """Mark an email as read."""
        try:
            if not self.imap:
                await self.connect()

            result, data = self.imap.store(email_message.message_uid, '+FLAGS', r'(\Seen)')
            if result == 'OK':
                logger.info("Email marked as read", message_id=email_message.message_id)
                return True
            else:
                logger.error("Failed to mark email as read", message_id=email_message.message_id)
                return False

        except Exception as e:
            logger.error("Error marking email as read", error=str(e))
            return False

    async def delete_email(self, email_message: EmailMessage) -> bool:
        """Delete an email."""
        try:
            if not self.imap:
                await self.connect()

            # Mark for deletion
            result, data = self.imap.store(email_message.message_uid, '+FLAGS', r'(\Deleted)')
            if result == 'OK':
                # Expunge to actually delete
                self.imap.expunge()
                logger.info("Email deleted successfully", message_id=email_message.message_id)
                audit_logger.log_email_processed(
                    sender=email_message.sender,
                    subject=email_message.subject,
                    action="deleted"
                )
                return True
            else:
                logger.error("Failed to mark email for deletion", message_id=email_message.message_id)
                return False

        except Exception as e:
            logger.error("Error deleting email", error=str(e))
            return False

    async def move_to_folder(self, email_message: EmailMessage, folder: str) -> bool:
        """Move email to a different folder."""
        try:
            if not self.imap:
                await self.connect()

            # Copy to destination folder
            result = self.imap.copy(email_message.message_uid, folder)
            if result[0] == 'OK':
                # Mark original for deletion
                await self.delete_email(email_message)
                logger.info(
                    "Email moved to folder",
                    message_id=email_message.message_id,
                    folder=folder
                )
                return True
            else:
                logger.error(
                    "Failed to move email to folder",
                    message_id=email_message.message_id,
                    folder=folder
                )
                return False

        except Exception as e:
            logger.error("Error moving email to folder", error=str(e))
            return False

    async def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        try:
            if not self.imap:
                return {"connected": False, "authenticated": False}

            # Test connection by selecting inbox
            result, _ = self.imap.select("INBOX")
            return {
                "connected": True,
                "authenticated": result == 'OK',
                "server": self.imap_server,
                "email": self.email_address
            }

        except Exception:
            return {"connected": False, "authenticated": False}