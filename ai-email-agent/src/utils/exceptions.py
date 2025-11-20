"""Custom exception classes for the AI Email Agent."""


class EmailAgentException(Exception):
    """Base exception class for the email agent application."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class EmailConnectionError(EmailAgentException):
    """Raised when email connection fails."""

    def __init__(self, message: str = "Failed to connect to email server"):
        super().__init__(message, "EMAIL_CONNECTION_ERROR")


class EmailAuthenticationError(EmailAgentException):
    """Raised when email authentication fails."""

    def __init__(self, message: str = "Email authentication failed"):
        super().__init__(message, "EMAIL_AUTH_ERROR")


class EmailSendingError(EmailAgentException):
    """Raised when email sending fails."""

    def __init__(self, message: str = "Failed to send email"):
        super().__init__(message, "EMAIL_SEND_ERROR")


class EmailParsingError(EmailAgentException):
    """Raised when email content parsing fails."""

    def __init__(self, message: str = "Failed to parse email content"):
        super().__init__(message, "EMAIL_PARSE_ERROR")


class AIServiceError(EmailAgentException):
    """Raised when AI service operations fail."""

    def __init__(self, message: str = "AI service error occurred"):
        super().__init__(message, "AI_SERVICE_ERROR")


class AIModelNotFoundError(AIServiceError):
    """Raised when requested AI model is not available."""

    def __init__(self, model_name: str):
        message = f"AI model '{model_name}' not found"
        super().__init__(message)
        self.model_name = model_name


class AIResponseError(AIServiceError):
    """Raised when AI response generation fails."""

    def __init__(self, message: str = "Failed to generate AI response"):
        super().__init__(message, "AI_RESPONSE_ERROR")


class ConfigurationError(EmailAgentException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, "CONFIG_ERROR")


class SecurityError(EmailAgentException):
    """Raised when security violation is detected."""

    def __init__(self, message: str = "Security violation detected"):
        super().__init__(message, "SECURITY_ERROR")


class ContentFilterError(SecurityError):
    """Raised when content filtering blocks an operation."""

    def __init__(self, message: str = "Content blocked by security filter"):
        super().__init__(message, "CONTENT_FILTER_ERROR")


class ProcessingError(EmailAgentException):
    """Raised when email processing fails."""

    def __init__(self, message: str = "Email processing error"):
        super().__init__(message, "PROCESSING_ERROR")


class RateLimitError(EmailAgentException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_ERROR")


class SchedulerError(EmailAgentException):
    """Raised when scheduler operations fail."""

    def __init__(self, message: str = "Scheduler error occurred"):
        super().__init__(message, "SCHEDULER_ERROR")