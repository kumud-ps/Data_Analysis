import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from ..email.processor import EmailProcessor
from ..config.settings import get_settings
from ..utils.logger import get_logger, audit_logger
from ..utils.exceptions import SchedulerError, ProcessingError

logger = get_logger(__name__)
settings = get_settings()


class EmailMonitor:
    """Automated email monitoring and processing scheduler."""

    def __init__(self, email_processor: EmailProcessor = None):
        """Initialize email monitor."""
        self.email_processor = email_processor or EmailProcessor()
        self.scheduler = None
        self.is_running = False
        self.monitoring_job_id = None
        self.last_check_time = None
        self.processing_history = []
        self.max_history_entries = 100

        # Job configuration
        self.check_interval = settings.processing.check_interval_minutes
        self.max_emails_per_check = settings.processing.max_emails_per_batch

    async def initialize(self) -> bool:
        """Initialize the scheduler and email processor."""
        try:
            logger.info("Initializing email monitor")

            # Initialize email processor
            processor_initialized = await self.email_processor.initialize()
            if not processor_initialized:
                logger.error("Failed to initialize email processor")
                return False

            # Configure scheduler
            self.scheduler = AsyncIOScheduler(
                jobstores={'default': MemoryJobStore()},
                executors={'default': AsyncIOExecutor()},
                timezone='UTC'
            )

            logger.info("Email monitor initialized successfully")
            return True

        except Exception as e:
            logger.error("Failed to initialize email monitor", error=str(e))
            raise SchedulerError(f"Monitor initialization failed: {str(e)}")

    async def start_monitoring(self, interval_minutes: int = None) -> bool:
        """Start automated email monitoring."""
        try:
            if self.is_running:
                logger.warning("Email monitoring is already running")
                return True

            if not self.scheduler:
                await self.initialize()

            # Use provided interval or default
            interval = interval_minutes or self.check_interval

            # Schedule email monitoring job
            self.monitoring_job_id = self.scheduler.add_job(
                func=self._monitor_and_process_emails,
                trigger=IntervalTrigger(minutes=interval),
                id='email_monitor',
                name='Email Monitoring',
                replace_existing=True,
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5 minutes grace period
            )

            # Start the scheduler
            self.scheduler.start()
            self.is_running = True

            logger.info(
                "Email monitoring started",
                interval_minutes=interval,
                job_id=self.monitoring_job_id
            )

            # Log the start
            audit_logger.log_email_processed(
                sender="system",
                subject="Email monitoring started",
                action="monitoring_started"
            )

            return True

        except Exception as e:
            logger.error("Failed to start email monitoring", error=str(e))
            raise SchedulerError(f"Failed to start monitoring: {str(e)}")

    async def stop_monitoring(self) -> bool:
        """Stop automated email monitoring."""
        try:
            if not self.is_running:
                logger.warning("Email monitoring is not running")
                return True

            # Stop the scheduler
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                self.scheduler = None

            self.is_running = False
            self.monitoring_job_id = None

            logger.info("Email monitoring stopped")

            # Log the stop
            audit_logger.log_email_processed(
                sender="system",
                subject="Email monitoring stopped",
                action="monitoring_stopped"
            )

            return True

        except Exception as e:
            logger.error("Failed to stop email monitoring", error=str(e))
            raise SchedulerError(f"Failed to stop monitoring: {str(e)}")

    async def schedule_immediate_check(self, delay_seconds: int = 10) -> str:
        """Schedule an immediate email check with optional delay."""
        try:
            if not self.scheduler:
                await self.initialize()

            # Schedule immediate check
            job_id = f"immediate_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.scheduler.add_job(
                func=self._monitor_and_process_emails,
                trigger='date',
                run_date=datetime.now() + timedelta(seconds=delay_seconds),
                id=job_id,
                name=f'Immediate Email Check - {job_id}',
                max_instances=1
            )

            logger.info("Immediate email check scheduled", delay_seconds=delay_seconds, job_id=job_id)
            return job_id

        except Exception as e:
            logger.error("Failed to schedule immediate check", error=str(e))
            raise SchedulerError(f"Failed to schedule immediate check: {str(e)}")

    async def schedule_custom_job(
        self,
        func: Callable,
        cron_expression: str = None,
        interval_minutes: int = None,
        job_id: str = None,
        **kwargs
    ) -> str:
        """Schedule a custom job."""
        try:
            if not self.scheduler:
                await self.initialize()

            # Determine trigger
            if cron_expression:
                trigger = CronTrigger.from_crontab(cron_expression)
            elif interval_minutes:
                trigger = IntervalTrigger(minutes=interval_minutes)
            else:
                raise SchedulerError("Either cron_expression or interval_minutes must be provided")

            # Generate job ID if not provided
            if not job_id:
                job_id = f"custom_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Schedule the job
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                name=f'Custom Job - {job_id}',
                kwargs=kwargs,
                max_instances=1,
                coalesce=True
            )

            logger.info("Custom job scheduled", job_id=job_id, trigger=trigger)
            return job_id

        except Exception as e:
            logger.error("Failed to schedule custom job", error=str(e))
            raise SchedulerError(f"Failed to schedule custom job: {str(e)}")

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        try:
            if not self.scheduler:
                logger.warning("Scheduler not initialized")
                return False

            self.scheduler.remove_job(job_id)
            logger.info("Job cancelled successfully", job_id=job_id)
            return True

        except Exception as e:
            logger.error("Failed to cancel job", job_id=job_id, error=str(e))
            return False

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics."""
        try:
            status = {
                'is_running': self.is_running,
                'check_interval_minutes': self.check_interval,
                'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'next_check_time': None,
                'active_jobs': [],
                'processing_stats': await self.email_processor.get_processing_stats(),
                'recent_processing_history': self.processing_history[-10:]  # Last 10 entries
            }

            # Get scheduled jobs
            if self.scheduler:
                jobs = self.scheduler.get_jobs()
                status['active_jobs'] = [
                    {
                        'id': job.id,
                        'name': job.name,
                        'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger)
                    }
                    for job in jobs
                ]

                # Find next monitoring check time
                monitor_job = next((job for job in jobs if job.id == 'email_monitor'), None)
                if monitor_job and monitor_job.next_run_time:
                    status['next_check_time'] = monitor_job.next_run_time.isoformat()

            return status

        except Exception as e:
            logger.error("Failed to get monitoring status", error=str(e))
            return {'error': str(e)}

    async def update_check_interval(self, interval_minutes: int) -> bool:
        """Update the email checking interval."""
        try:
            if interval_minutes < 1:
                raise SchedulerError("Check interval must be at least 1 minute")

            self.check_interval = interval_minutes

            # Update the job if monitoring is running
            if self.is_running and self.scheduler and self.monitoring_job_id:
                # Remove current job
                self.scheduler.remove_job(self.monitoring_job_id)

                # Add new job with updated interval
                self.monitoring_job_id = self.scheduler.add_job(
                    func=self._monitor_and_process_emails,
                    trigger=IntervalTrigger(minutes=interval),
                    id='email_monitor',
                    name='Email Monitoring',
                    replace_existing=True,
                    max_instances=1,
                    coalesce=True
                )

                logger.info("Check interval updated", new_interval=interval_minutes)
                return True

            else:
                logger.info("Check interval setting updated", new_interval=interval_minutes)
                return True

        except Exception as e:
            logger.error("Failed to update check interval", error=str(e))
            raise SchedulerError(f"Failed to update interval: {str(e)}")

    async def _monitor_and_process_emails(self):
        """Internal method to monitor and process emails."""
        try:
            start_time = datetime.now()
            logger.info("Starting scheduled email processing")

            # Process emails
            result = await self.email_processor.process_emails(
                limit=self.max_emails_per_check,
                dry_run=False
            )

            # Update last check time
            self.last_check_time = datetime.now()

            # Add to processing history
            history_entry = {
                'timestamp': start_time.isoformat(),
                'processed': result.get('processed', 0),
                'responded': result.get('responded', 0),
                'skipped': result.get('skipped', 0),
                'errors': result.get('errors', 0),
                'processing_time': result.get('processing_time', 0)
            }

            self.processing_history.append(history_entry)

            # Limit history size
            if len(self.processing_history) > self.max_history_entries:
                self.processing_history = self.processing_history[-self.max_history_entries:]

            logger.info(
                "Scheduled email processing completed",
                **history_entry
            )

        except ProcessingError as e:
            logger.error("Email processing error during scheduled run", error=str(e))
            audit_logger.log_error(
                error_type="scheduled_processing_error",
                details={"error": str(e)}
            )

        except Exception as e:
            logger.error("Unexpected error during scheduled email processing", error=str(e))
            audit_logger.log_error(
                error_type="scheduled_processing_unexpected_error",
                details={"error": str(e)}
            )

    async def run_health_check(self) -> Dict[str, Any]:
        """Run a comprehensive health check of the monitoring system."""
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'monitoring_active': self.is_running,
                'scheduler_status': 'running' if self.scheduler and self.scheduler.running else 'stopped',
                'email_processor_status': 'unknown',
                'last_check_successful': None,
                'time_since_last_check': None,
                'active_jobs_count': 0,
                'recent_errors': []
            }

            # Check scheduler status
            if self.scheduler:
                jobs = self.scheduler.get_jobs()
                health_status['active_jobs_count'] = len(jobs)

            # Check time since last check
            if self.last_check_time:
                time_since = datetime.now() - self.last_check_time
                health_status['time_since_last_check'] = str(time_since)
                health_status['last_check_successful'] = time_since < timedelta(hours=1)

            # Check email processor
            try:
                processor_stats = await self.email_processor.get_processing_stats()
                health_status['email_processor_status'] = 'ready'
                health_status['processing_stats'] = processor_stats
            except Exception as e:
                health_status['email_processor_status'] = 'error'
                health_status['recent_errors'].append(str(e))

            # Overall health assessment
            health_status['overall_health'] = (
                health_status['monitoring_active'] and
                health_status['scheduler_status'] == 'running' and
                health_status['email_processor_status'] == 'ready'
            )

            return health_status

        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_health': False,
                'error': str(e)
            }

    async def cleanup(self):
        """Clean up scheduler resources."""
        try:
            await self.stop_monitoring()
            await self.email_processor.cleanup()
            logger.info("Email monitor cleanup completed")
        except Exception as e:
            logger.error("Error during monitor cleanup", error=str(e))