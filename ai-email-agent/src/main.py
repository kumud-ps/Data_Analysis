from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import os

from .config.settings import get_settings
from .scheduler.email_monitor import EmailMonitor
from .email.processor import EmailProcessor
from .utils.logger import get_logger, setup_logging
from .utils.exceptions import EmailAgentException

# Setup logging
settings = get_settings()
setup_logging(
    log_level=settings.security.log_level,
    enable_audit=settings.security.enable_audit_log
)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Email Agent API",
    description="Automated email processing with AI-powered responses",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
email_monitor = None
email_processor = None


# Pydantic models for API
class EmailProcessingRequest(BaseModel):
    limit: Optional[int] = Field(None, ge=1, le=100, description="Maximum emails to process")
    sender_filter: Optional[str] = Field(None, description="Filter by sender email")
    dry_run: bool = Field(False, description="Run in dry-run mode (don't send responses)")


class EmailProcessingResponse(BaseModel):
    processed: int = Field(..., description="Number of emails processed")
    responded: int = Field(..., description="Number of responses sent")
    skipped: int = Field(..., description="Number of emails skipped")
    errors: int = Field(..., description="Number of processing errors")
    processing_time: float = Field(..., description="Total processing time in seconds")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed processing results")


class MonitoringConfigRequest(BaseModel):
    interval_minutes: int = Field(..., ge=1, le=1440, description="Check interval in minutes")
    max_emails_per_check: Optional[int] = Field(None, ge=1, le=100, description="Max emails per check")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    details: Dict[str, Any] = Field(..., description="Detailed health information")


class StatusResponse(BaseModel):
    monitoring_active: bool = Field(..., description="Whether monitoring is currently active")
    last_check_time: Optional[datetime] = Field(None, description="Last email check time")
    next_check_time: Optional[datetime] = Field(None, description="Next scheduled check time")
    processing_stats: Dict[str, int] = Field(..., description="Processing statistics")
    active_jobs: List[Dict[str, Any]] = Field(..., description="Active scheduled jobs")


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    global email_monitor, email_processor

    try:
        logger.info("Starting AI Email Agent API")

        # Initialize components
        email_processor = EmailProcessor()
        email_monitor = EmailMonitor(email_processor)

        # Initialize email monitor
        await email_monitor.initialize()

        logger.info("AI Email Agent API started successfully")

    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        # Continue startup - we can still serve API endpoints even if email services fail


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    global email_monitor, email_processor

    try:
        logger.info("Shutting down AI Email Agent API")

        if email_monitor:
            await email_monitor.cleanup()

        logger.info("AI Email Agent API shutdown completed")

    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Dependency to get email monitor instance
async def get_email_monitor() -> EmailMonitor:
    """Get email monitor instance."""
    global email_monitor
    if not email_monitor:
        email_monitor = EmailMonitor()
        await email_monitor.initialize()
    return email_monitor


# API Endpoints
@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI Email Agent API",
        "version": "1.0.0",
        "description": "Automated email processing with AI-powered responses",
        "docs": "/docs",
        "health": "/health",
        "status": "/status"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(monitor: EmailMonitor = Depends(get_email_monitor)):
    """Comprehensive health check endpoint."""
    try:
        health_data = await monitor.run_health_check()

        return HealthCheckResponse(
            status="healthy" if health_data.get('overall_health') else "unhealthy",
            timestamp=datetime.now(),
            details=health_data
        )

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthCheckResponse(
            status="error",
            timestamp=datetime.now(),
            details={"error": str(e)}
        )


@app.get("/status", response_model=StatusResponse)
async def get_status(monitor: EmailMonitor = Depends(get_email_monitor)):
    """Get current monitoring status and statistics."""
    try:
        status_data = await monitor.get_monitoring_status()

        return StatusResponse(
            monitoring_active=status_data.get('is_running', False),
            last_check_time=datetime.fromisoformat(status_data['last_check_time']) if status_data.get('last_check_time') else None,
            next_check_time=datetime.fromisoformat(status_data['next_check_time']) if status_data.get('next_check_time') else None,
            processing_stats=status_data.get('processing_stats', {}),
            active_jobs=status_data.get('active_jobs', [])
        )

    except Exception as e:
        logger.error("Failed to get status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@app.post("/monitoring/start")
async def start_monitoring(
    interval_minutes: int = Field(None, ge=1, le=1440),
    monitor: EmailMonitor = Depends(get_email_monitor)
):
    """Start automated email monitoring."""
    try:
        success = await monitor.start_monitoring(interval_minutes)

        if success:
            return {"message": "Email monitoring started successfully", "interval_minutes": interval_minutes}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start email monitoring"
            )

    except Exception as e:
        logger.error("Failed to start monitoring", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@app.post("/monitoring/stop")
async def stop_monitoring(monitor: EmailMonitor = Depends(get_email_monitor)):
    """Stop automated email monitoring."""
    try:
        success = await monitor.stop_monitoring()

        if success:
            return {"message": "Email monitoring stopped successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop email monitoring"
            )

    except Exception as e:
        logger.error("Failed to stop monitoring", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@app.post("/monitoring/update-interval")
async def update_check_interval(
    interval_minutes: int = Field(..., ge=1, le=1440),
    monitor: EmailMonitor = Depends(get_email_monitor)
):
    """Update the email checking interval."""
    try:
        success = await monitor.update_check_interval(interval_minutes)

        if success:
            return {"message": "Check interval updated successfully", "interval_minutes": interval_minutes}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update check interval"
            )

    except Exception as e:
        logger.error("Failed to update check interval", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update interval: {str(e)}"
        )


@app.post("/emails/process", response_model=EmailProcessingResponse)
async def process_emails(
    request: EmailProcessingRequest,
    background_tasks: BackgroundTasks,
    monitor: EmailMonitor = Depends(get_email_monitor)
):
    """Manually trigger email processing."""
    try:
        # Process emails
        result = await monitor.email_processor.process_emails(
            limit=request.limit,
            sender_filter=request.sender_filter,
            dry_run=request.dry_run
        )

        return EmailProcessingResponse(**result)

    except Exception as e:
        logger.error("Manual email processing failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email processing failed: {str(e)}"
        )


@app.post("/emails/process-background")
async def process_emails_background(
    request: EmailProcessingRequest,
    background_tasks: BackgroundTasks,
    monitor: EmailMonitor = Depends(get_email_monitor)
):
    """Trigger email processing in the background."""
    try:
        # Add background task
        background_tasks.add_task(
            monitor.email_processor.process_emails,
            limit=request.limit,
            sender_filter=request.sender_filter,
            dry_run=request.dry_run
        )

        return {"message": "Email processing started in background"}

    except Exception as e:
        logger.error("Failed to start background email processing", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start background processing: {str(e)}"
        )


@app.post("/emails/check-immediate")
async def check_emails_immediate(
    delay_seconds: int = Field(10, ge=0, le=300),
    monitor: EmailMonitor = Depends(get_email_monitor)
):
    """Schedule an immediate email check."""
    try:
        job_id = await monitor.schedule_immediate_check(delay_seconds)

        return {"message": "Immediate email check scheduled", "job_id": job_id, "delay_seconds": delay_seconds}

    except Exception as e:
        logger.error("Failed to schedule immediate check", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule immediate check: {str(e)}"
        )


@app.get("/stats")
async def get_processing_stats(monitor: EmailMonitor = Depends(get_email_monitor)):
    """Get processing statistics."""
    try:
        stats = await monitor.email_processor.get_processing_stats()
        return {"stats": stats}

    except Exception as e:
        logger.error("Failed to get processing stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/stats/reset")
async def reset_processing_stats(monitor: EmailMonitor = Depends(get_email_monitor)):
    """Reset processing statistics."""
    try:
        await monitor.email_processor.reset_stats()
        return {"message": "Processing statistics reset successfully"}

    except Exception as e:
        logger.error("Failed to reset stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset stats: {str(e)}"
        )


@app.get("/config")
async def get_configuration():
    """Get current configuration (excluding sensitive data)."""
    try:
        config = {
            "email": {
                "imap_server": settings.email.imap_server,
                "imap_port": settings.email.imap_port,
                "smtp_server": settings.email.smtp_server,
                "smtp_port": settings.email.smtp_port,
                "use_tls": settings.email.use_tls
            },
            "ai": {
                "ollama_base_url": settings.ai.ollama_base_url,
                "model_name": settings.ai.model_name,
                "temperature": settings.ai.temperature,
                "max_tokens": settings.ai.max_tokens,
                "timeout": settings.ai.timeout
            },
            "processing": {
                "auto_reply_enabled": settings.processing.auto_reply_enabled,
                "delete_processed": settings.processing.delete_processed,
                "max_emails_per_batch": settings.processing.max_emails_per_batch,
                "check_interval_minutes": settings.processing.check_interval_minutes,
                "quiet_hours_start": settings.processing.quiet_hours_start,
                "quiet_hours_end": settings.processing.quiet_hours_end
            },
            "security": {
                "enable_content_filter": settings.security.enable_content_filter,
                "max_attachment_size_mb": settings.security.max_attachment_size_mb,
                "log_level": settings.security.log_level,
                "enable_audit_log": settings.security.enable_audit_log
            },
            "api": {
                "host": settings.api.host,
                "port": settings.api.port,
                "debug": settings.api.debug,
                "cors_origins": settings.api.cors_origins
            }
        }

        return {"config": config}

    except Exception as e:
        logger.error("Failed to get configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@app.exception_handler(EmailAgentException)
async def email_agent_exception_handler(request, exc: EmailAgentException):
    """Handle custom email agent exceptions."""
    logger.error("Email agent exception", error=str(exc), error_code=exc.error_code)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Email agent error",
            "message": exc.message,
            "error_code": exc.error_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error("Unexpected error", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "src.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level=settings.security.log_level.lower()
    )