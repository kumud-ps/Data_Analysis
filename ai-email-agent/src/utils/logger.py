import logging
import structlog
import sys
from typing import Any, Dict
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", enable_audit: bool = True) -> None:
    """Setup structured logging for the application."""
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Add file handler for audit logs if enabled
    if enable_audit:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        audit_handler = logging.FileHandler(
            log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        )
        audit_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        audit_handler.setFormatter(formatter)

        # Get root logger and add handler
        root_logger = logging.getLogger()
        root_logger.addHandler(audit_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class AuditLogger:
    """Specialized logger for audit events."""

    def __init__(self):
        self.logger = get_logger("audit")

    def log_email_received(self, sender: str, subject: str, message_id: str) -> None:
        """Log email received event."""
        self.logger.info(
            "email_received",
            sender=sender,
            subject=subject,
            message_id=message_id,
            timestamp=datetime.now().isoformat()
        )

    def log_email_processed(self, sender: str, subject: str, action: str) -> None:
        """Log email processed event."""
        self.logger.info(
            "email_processed",
            sender=sender,
            subject=subject,
            action=action,
            timestamp=datetime.now().isoformat()
        )

    def log_email_sent(self, recipient: str, subject: str, success: bool) -> None:
        """Log email sent event."""
        self.logger.info(
            "email_sent",
            recipient=recipient,
            subject=subject,
            success=success,
            timestamp=datetime.now().isoformat()
        )

    def log_ai_response(self, sender: str, model: str, tokens_used: int) -> None:
        """Log AI response generated."""
        self.logger.info(
            "ai_response_generated",
            sender=sender,
            model=model,
            tokens_used=tokens_used,
            timestamp=datetime.now().isoformat()
        )

    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security-related events."""
        self.logger.warning(
            "security_event",
            event_type=event_type,
            details=details,
            timestamp=datetime.now().isoformat()
        )

    def log_error(self, error_type: str, details: Dict[str, Any]) -> None:
        """Log application errors."""
        self.logger.error(
            "application_error",
            error_type=error_type,
            details=details,
            timestamp=datetime.now().isoformat()
        )


# Global audit logger instance
audit_logger = AuditLogger()