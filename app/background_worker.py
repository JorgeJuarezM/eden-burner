"""
Background worker for EPSON PP-100 Disc Burner Application
Handles job processing when GUI is closed
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

import schedule

import db
from app.graphql_client import SyncGraphQLClient
from app.job_queue import JobQueue, JobStatus
from app.local_storage import LocalStorage
from config.config import Config

app_config = Config.get_current_config()


class BackgroundWorker:
    """Background worker that manages job processing and API polling."""

    def __init__(self, job_queue: JobQueue):
        """Initialize background worker.

        Args:
            config: Application configuration
            job_queue: Job queue instance
        """
        self.job_queue = job_queue
        self.logger = logging.getLogger(__name__)

        # Components
        self.download_manager = job_queue.download_manager
        self.storage = LocalStorage()
        self.graphql_client = SyncGraphQLClient()

        # Control flags
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None

        # Last check time for API polling
        self.last_api_check: Optional[datetime] = None

        # Setup scheduler for periodic tasks
        self.setup_scheduler()

    def setup_scheduler(self):
        """Setup the task scheduler."""
        # Schedule API checks
        schedule.every(app_config.check_interval).seconds.do(self.check_for_new_isos)

        # Schedule cleanup tasks
        schedule.every(1).hours.do(self.cleanup_old_jobs)
        schedule.every(6).hours.do(self.cleanup_download_manager)

        # Schedule database maintenance
        schedule.every(24).hours.do(self.database_maintenance)

    def start(self):
        """Start the background worker."""
        if self.running:
            self.logger.warning("Background worker already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Background worker started")

    def stop(self):
        """Stop the background worker."""
        if not self.running:
            return

        self.running = False

        # Clear scheduled jobs
        schedule.clear()

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)

        self.logger.info("Background worker stopped")

    def _worker_loop(self):
        """Main worker loop."""
        try:
            while self.running:
                # Run scheduled tasks
                schedule.run_pending()

                # Process job queue
                self._process_job_queue()

                # Brief pause to prevent busy waiting
                time.sleep(10)

        except Exception as e:
            self.logger.error(f"Error in background worker loop: {e}")
        finally:
            self.logger.info("Background worker loop ended")

    def _process_job_queue(self):
        """Process the job queue."""
        try:
            # Get next job to process (for new jobs or pending jobs)
            job = self.job_queue.get_next_job()

            if job:
                self.logger.debug(f"Processing job: {job.id}")
                self.job_queue.start_job_processing(job)

                # After processing, check if job is ready for next stage
                # self._check_job_stage_progression(job)

            # Also check for jobs that are ready for next stage
            self._check_ready_jobs()

        except Exception as e:
            self.logger.error(f"Error processing job queue: {e}")

    def _check_ready_jobs(self):
        """Check for jobs that are ready for next processing stage."""
        try:
            # Get all jobs that are ready for next stage
            ready_jobs = [
                job
                for job in self.job_queue.get_all_jobs()
                if job.status
                in [JobStatus.DOWNLOADED, JobStatus.JDF_READY, JobStatus.QUEUED_FOR_BURNING]
            ]

            for job in ready_jobs:
                # Check if we can start this job (enough capacity)
                active_jobs = len(
                    [
                        j
                        for j in self.job_queue.get_all_jobs()
                        if j.status
                        in [JobStatus.DOWNLOADING, JobStatus.BURNING, JobStatus.VERIFYING]
                    ]
                )
                if active_jobs < app_config.max_concurrent_jobs:
                    self.logger.debug(f"Processing ready job {job.id} for next stage")
                    self.job_queue.start_job_processing(job)
                    break  # Process one at a time

        except Exception as e:
            self.logger.error(f"Error checking ready jobs: {e}")

    def _check_job_stage_progression(self, job):
        """Check if job is ready for next processing stage."""
        try:
            # The _check_ready_jobs method will handle this more efficiently
            # Just trigger a check in the next iteration
            pass
        except Exception as e:
            self.logger.error(f"Error checking job stage progression: {e}")

    def check_for_new_isos(self) -> bool:
        """Check for new ISO files from API.

        Returns:
            True if new ISOs found and added, False otherwise
        """
        try:
            # Format last check time for API
            last_check_str = None
            if self.last_api_check:
                last_check_str = self.last_api_check.isoformat()

            # Query for new ISOs
            new_isos = self.graphql_client.query_new_isos(last_check_str)

            if not new_isos:
                self.logger.debug("No new ISOs found")
                return False

            # Add new ISOs as jobs
            added_count = 0
            for iso_info in new_isos:
                self.logger.info("New ISO found: %s", iso_info.get("id"))
                try:
                    # Check if we already have this ISO
                    existing_jobs = [
                        job
                        for job in self.job_queue.get_all_jobs()
                        if job.iso_info.get("id") == iso_info.get("id")
                    ]

                    if not existing_jobs:
                        # Add as new job
                        job_id = self.job_queue.add_job(iso_info)
                        db.BurnJob.save_job(job_id, iso_info)
                        added_count += 1
                        self.logger.info(f"Added job {job_id} for ISO {iso_info.get('id')}")

                except Exception as e:
                    self.logger.error(f"Error adding job for ISO {iso_info.get('id')}: {e}")

            if added_count > 0:
                self.logger.info(f"Added {added_count} new jobs from API")

            # Update last check time
            self.last_api_check = datetime.now()

            return added_count > 0

        except Exception as e:
            self.logger.error(f"Error checking for new ISOs: {e}")
            return False

    def cleanup_old_jobs(self):
        """Clean up old completed and failed jobs."""
        try:
            # Clean from storage
            deleted_count = db.BurnJob.cleanup_old_jobs(max_age_days=7)

            # Clean from job queue (in-memory cleanup)
            self.job_queue.cleanup_completed_jobs(max_age_days=7)

            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old jobs")

        except Exception as e:
            self.logger.error(f"Error cleaning up old jobs: {e}")

    def cleanup_download_manager(self):
        """Clean up old downloads from memory."""
        try:
            self.download_manager.cleanup_old_downloads(max_age_hours=24)
        except Exception as e:
            self.logger.error(f"Error cleaning up download manager: {e}")

    def database_maintenance(self):
        """Perform database maintenance tasks."""
        try:
            # Create backup
            backup_path = self.storage.backup_database()
            if backup_path:
                self.logger.info(f"Created database backup: {backup_path}")

            # Clean up old backups
            deleted_backups = self.storage.cleanup_old_backups()
            if deleted_backups > 0:
                self.logger.info(f"Cleaned up {deleted_backups} old backups")

            # Get storage stats
            stats = db.BurnJob.get_storage_stats()
            self.logger.info(f"Storage stats: {stats}")

        except Exception as e:
            self.logger.error(f"Error in database maintenance: {e}")

    def get_worker_status(self) -> Dict[str, Any]:
        """Get current worker status.

        Returns:
            Dictionary with worker status information
        """
        try:
            queue_status = self.job_queue.get_queue_status()
            storage_stats = db.BurnJob.get_storage_stats()
            download_stats = self.download_manager.get_download_stats()

            return {
                "running": self.running,
                "last_api_check": self.last_api_check.isoformat() if self.last_api_check else None,
                "next_api_check_in": self._get_next_api_check_time(),
                "queue_status": queue_status,
                "storage_stats": storage_stats,
                "download_stats": download_stats,
                "scheduled_jobs": len(schedule.get_jobs()),
            }

        except Exception as e:
            self.logger.error(f"Error getting worker status: {e}")
            return {"error": str(e)}

    def _get_next_api_check_time(self) -> Optional[int]:
        """Get time until next API check in seconds."""
        try:
            # Find next scheduled API check
            for job in schedule.get_jobs():
                if hasattr(job, "job_func") and job.job_func.__name__ == "check_for_new_isos":
                    next_run = job.next_run
                    if next_run:
                        remaining = (next_run - datetime.now()).total_seconds()
                        return max(0, int(remaining))

            return None

        except Exception:
            return None

    def trigger_api_check_now(self) -> bool:
        """Trigger an immediate API check.

        Returns:
            True if check was successful, False otherwise
        """
        try:
            return self.check_for_new_isos()
        except Exception as e:
            self.logger.error(f"Error in manual API check: {e}")
            return False

    def pause_worker(self, duration_minutes: int = 60):
        """Pause the worker for a specified duration.

        Args:
            duration_minutes: Duration to pause in minutes
        """
        # This could be implemented to pause API checks and job processing
        # For now, it's a placeholder
        self.logger.info(f"Worker pause requested for {duration_minutes} minutes")

    def resume_worker(self):
        """Resume the worker after a pause."""
        # This could be implemented to resume paused operations
        self.logger.info("Worker resume requested")

    def export_worker_data(self, export_path: str) -> bool:
        """Export worker data to file.

        Args:
            export_path: Path to export file

        Returns:
            True if exported successfully
        """
        try:
            status = self.get_worker_status()

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2, default=str)

            self.logger.info(f"Exported worker status to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting worker data: {e}")
            return False
