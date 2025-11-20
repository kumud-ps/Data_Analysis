import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class EmailSettings(BaseSettings):
    """Email service configuration."""
    gmail_username: str = Field(..., description="Gmail email address")
    gmail_app_password: str = Field(..., description="Gmail app password")
    imap_server: str = Field("imap.gmail.com", description="IMAP server address")
    imap_port: int = Field(993, description="IMAP server port")
    smtp_server: str = Field("smtp.gmail.com", description="SMTP server address")
    smtp_port: int = Field(587, description="SMTP server port")
    use_tls: bool = Field(True, description="Use TLS for SMTP")

    class Config:
        env_prefix = "EMAIL_"


class AISettings(BaseSettings):
    """AI service configuration."""
    ollama_base_url: str = Field("http://localhost:11434", description="Ollama API base URL")
    model_name: str = Field("llama3.2:1b", description="Ollama model name")
    temperature: float = Field(0.7, description="AI response temperature")
    max_tokens: int = Field(500, description="Maximum tokens for AI response")
    timeout: int = Field(30, description="Request timeout in seconds")

    class Config:
        env_prefix = "AI_"


class ProcessingSettings(BaseSettings):
    """Email processing configuration."""
    auto_reply_enabled: bool = Field(True, description="Enable automatic replies")
    delete_processed: bool = Field(True, description="Delete processed emails")
    max_emails_per_batch: int = Field(10, description="Maximum emails to process at once")
    check_interval_minutes: int = Field(5, description="Email checking interval")
    quiet_hours_start: str = Field("22:00", description="Quiet hours start time")
    quiet_hours_end: str = Field("08:00", description="Quiet hours end time")
    allowed_senders: Optional[List[str]] = Field(None, description="Whitelist of allowed sender emails")
    blocked_senders: Optional[List[str]] = Field(None, description="Blacklist of blocked sender emails")

    class Config:
        env_prefix = "PROCESSING_"


class SecuritySettings(BaseSettings):
    """Security configuration."""
    enable_content_filter: bool = Field(True, description="Enable content filtering")
    max_attachment_size_mb: int = Field(5, description="Maximum attachment size in MB")
    log_level: str = Field("INFO", description="Logging level")
    enable_audit_log: bool = Field(True, description="Enable audit logging")

    class Config:
        env_prefix = "SECURITY_"


class APISettings(BaseSettings):
    """API configuration."""
    host: str = Field("0.0.0.0", description="API host")
    port: int = Field(8000, description="API port")
    debug: bool = Field(False, description="Enable debug mode")
    cors_origins: List[str] = Field(["*"], description="CORS allowed origins")

    class Config:
        env_prefix = "API_"


class Settings(BaseSettings):
    """Main application settings."""
    email: EmailSettings = Field(default_factory=EmailSettings)
    ai: AISettings = Field(default_factory=AISettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    api: APISettings = Field(default_factory=APISettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings