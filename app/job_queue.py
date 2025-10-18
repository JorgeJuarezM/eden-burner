"""
Job Queue Management System for EPSON PP-100 Disc Burner Application

This module implements a sophisticated job queue management system that handles
the entire lifecycle of ISO burning jobs from discovery to completion.

Architecture:
    - Multi-threaded job processing with configurable concurrency
    - State machine pattern for job status transitions
    - Event-driven architecture with callback notifications
    - Integration with database, file system, and robot communication

Components:
    - BurnJob: Data class representing individual burning jobs
    - JobStatus: Enumeration of all possible job states
    - JobQueue: Thread-safe queue manager with processing logic
    - Integration with ISODownloadManager, JDFGenerator, and GraphQL API

Job Lifecycle:
    1. PENDING → DOWNLOADING → DOWNLOADED → GENERATING_JDF → JDF_READY
    2. JDF_READY → QUEUED_FOR_BURNING → BURNING → VERIFYING → COMPLETED
    3. Any state → FAILED (with retry capability)
    4. Any active state → CANCELLED (user-initiated)

Features:
    - Automatic disc type detection (CD/DVD) based on file size
    - Progress tracking and status updates
    - Retry mechanism for failed jobs
    - Concurrent job processing with configurable limits
    - Integration with robot status files (.INP, .DON, .ERR)
    - Automatic file management (downloads, JDF files, completed jobs)
    - DICOM study information extraction and display

Threading Model:
    - Main thread: GUI interactions and job queue management
    - Background threads: Individual job processing (download, burn, verify)
    - Worker threads: Specific task execution with proper synchronization

Error Handling:
    - Comprehensive error logging and user notifications
    - Graceful degradation on component failures
    - Automatic retry with exponential backoff
    - Detailed error messages for troubleshooting
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.graphql_client import SyncGraphQLClient
from app.iso_downloader import ISODownloadManager
from app.jdf_generator import JDFGenerator
from config.config import Config
from services.jdf_handler import JDFHandler

app_config = Config.get_current_config()


class JobStatus(Enum):
    """Job status enumeration."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    GENERATING_JDF = "generating_jdf"
    JDF_READY = "jdf_ready"
    QUEUED_FOR_BURNING = "queued_for_burning"
    BURNING = "burning"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BurnJob:
    """Represents a disc burning job."""

    id: str
    iso_info: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # File paths
    iso_path: Optional[str] = None
    jdf_path: Optional[str] = None

    # Progress tracking
    progress: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0

    # Robot interaction
    robot_job_id: Optional[str] = None
    estimated_completion: Optional[datetime] = None

    # Notification tracking
    notification_sent: bool = False

    # Disc type detection
    disc_type: Optional[str] = None  # "CD" or "DVD" or None if unknown

    def detect_disc_type(self, file_path: str, job_queue: "JobQueue") -> str:
        """Detect disc type based on file size.

        Args:
            file_path: Path to the ISO file

        Returns:
            "CD" for files under 700MB, "DVD" for files between 700MB and 4.5GB,
            "Invalid" for files over 4.5GB, "Unknown" for errors
        """
        try:
            file_size = Path(file_path).stat().st_size
            size_mb = file_size / (1024 * 1024)  # Convert to MB

            if size_mb < 700:
                return "CD"
            elif size_mb <= (4.5 * 1024):
                return "DVD"
            else:
                raise Exception(f"File size exceeds 4.5GB")
        except Exception as e:
            job_queue.logger.error(f"Error detecting disc type for file {file_path}: {e}")
            raise

    def update_status(
        self,
        status: JobStatus,
        error_message: Optional[str] = None,
        job_queue: Optional["JobQueue"] = None,
    ):
        """Update job status and timestamp."""
        if self.status == status:
            return

        self.status = status
        self.updated_at = datetime.now()
        self.error_message = error_message
        self.notification_sent = False  # Reset notification sent flag when status changes

        if job_queue and self.status in [
            JobStatus.COMPLETED,
            JobStatus.FAILED,
        ]:
            self.update_status_to_api(job_queue)

    def update_status_to_api(self, job_queue: "JobQueue"):
        """Update job status to API."""
        iso_id = self.iso_info["id"]

        # Map internal status to API status
        status_mapping = {
            JobStatus.COMPLETED: "COMPLETED",
            JobStatus.FAILED: "FAILED",
        }

        api_status = status_mapping.get(self.status)

        try:
            result = job_queue.graphql_client.update_download_iso_status(
                iso_id=iso_id,
                status_burn=api_status,
                error_message=self.error_message if self.status == JobStatus.FAILED else None,
            )

            if result.get("success"):
                job_queue.logger.info(f"Updated ISO {iso_id} status to {api_status} via API")
            else:
                job_queue.logger.error(
                    f"Failed to update ISO {iso_id} status via API: {result.get('errors', [])}"
                )

        except Exception as e:
            job_queue.logger.error(f"Error calling GraphQL mutation for ISO {iso_id}: {e}")

    def can_retry(self, max_retries: int) -> bool:
        """Check if job can be retried."""
        return self.retry_count < max_retries and self.status in [
            JobStatus.FAILED,
            JobStatus.COMPLETED,
        ]

    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.updated_at = datetime.now()


class JobQueue:
    """Thread-safe job queue for managing burning jobs."""

    def __init__(self):
        """
        Initialize the thread-safe job queue system.

        This constructor sets up the complete job queue infrastructure including:
        - Job storage and queue management
        - Thread synchronization primitives
        - Callback system for job status updates
        - Component integration (download manager, GraphQL client)
        - Progress callback registration

        The job queue manages the entire lifecycle of burning jobs from creation
        through completion, handling concurrent processing with proper synchronization.

        Thread Safety:
        - Uses RLock for thread-safe operations on shared data
        - All public methods are thread-safe
        - Callback execution is protected from exceptions

        Components Initialized:
        - ISODownloadManager: For file download operations
        - SyncGraphQLClient: For API communication
        - Progress callbacks: For download progress tracking
        """
        self.logger = logging.getLogger(__name__)

        # Job storage
        self.jobs: Dict[str, BurnJob] = {}
        self.job_queue: List[str] = []  # Queue of job IDs (FIFO order)

        # Threading
        self.lock = threading.RLock()

        # Callbacks
        self.job_update_callbacks: List[Callable[[BurnJob], None]] = []

        # Components
        self.download_manager = ISODownloadManager()
        self.graphql_client = SyncGraphQLClient()

        # Setup progress callbacks
        self.download_manager.add_progress_callback(self._on_download_progress)

    def add_job_update_callback(self, callback: Callable[[BurnJob], None]):
        """
        Register a callback function for job status updates.

        Callbacks are invoked whenever a job's status changes, allowing
        external components (like the GUI) to react to job progress.

        Args:
            callback: Function that accepts a BurnJob parameter and returns None.
                     The callback should handle its own error conditions.

        The callback system provides real-time job monitoring and enables
        responsive UI updates without tight coupling between components.
        """
        self.job_update_callbacks.append(callback)

    def remove_job_update_callback(self, callback: Callable[[BurnJob], None]):
        """
        Unregister a job update callback function.

        Removes a previously registered callback from the notification system.

        Args:
            callback: The callback function to remove (must be the same object reference)

        Returns:
            None

        Note:
            If the callback is not found in the list, this method silently succeeds
            to avoid errors when cleaning up callbacks.
        """
        if callback in self.job_update_callbacks:
            self.job_update_callbacks.remove(callback)

    def _notify_job_update(self, job: BurnJob):
        """Notify all callbacks of job update."""
        for callback in self.job_update_callbacks:
            try:
                callback(job)
            except Exception as e:
                self.logger.error(f"Error in job update callback: {e}")

    def add_job(self, iso_info: Dict[str, Any]) -> str:
        """
        Add a new burning job to the processing queue.

        This method creates a new BurnJob instance from ISO information and
        adds it to both the job storage and processing queue for subsequent
        execution through the job lifecycle pipeline.

        Args:
            iso_info (Dict[str, Any]): Complete ISO information from GraphQL API including:
                - id: Unique ISO identifier
                - filename: ISO file name
                - fileSize: Size in bytes
                - downloadUrl: URL for file download
                - checksum: File integrity check
                - study: DICOM study information (patient, dates, descriptions)

        Returns:
            str: Unique job ID (UUID) for the created job

        Process:
        1. Generate unique job ID using UUID4
        2. Create BurnJob instance with PENDING status
        3. Store job in internal jobs dictionary
        4. Add job ID to processing queue (FIFO order)
        5. Trigger callback notifications for job creation
        6. Log job creation for audit trail

        Thread Safety:
            Uses RLock to ensure atomic job creation and queue updates
        """
        job_id = str(uuid.uuid4())

        with self.lock:
            job = BurnJob(id=job_id, iso_info=iso_info)

            self.jobs[job_id] = job

            # Add to queue (FIFO order)
            self.job_queue.append(job_id)

            self.logger.info(f"Added job {job_id} for ISO {iso_info.get('id', 'unknown')}")
            self._notify_job_update(job)

        return job_id

    def get_next_job(self) -> Optional[BurnJob]:
        """
        Retrieve the next job ready for processing from the queue.

        This method implements a thread-safe job selection algorithm that:
        1. Examines jobs in FIFO order from the processing queue
        2. Validates job still exists in storage
        3. Skips cancelled, completed, or failed jobs
        4. Checks if job can be processed (capacity and status)
        5. Returns the first processable job or None if none available

        Returns:
            Optional[BurnJob]: Next job ready for processing, or None if queue is empty
                             or no jobs can be processed at this time.

        Algorithm:
        - Iterates through job_queue in FIFO order
        - Validates job exists in self.jobs dictionary
        - Filters out terminal state jobs (CANCELLED, COMPLETED, FAILED)
        - Checks processing capacity using _can_process_job()
        - Returns first valid job or None if no suitable jobs found

        Thread Safety:
            Uses RLock to prevent race conditions during queue examination
        """
        with self.lock:
            while self.job_queue:
                job_id = self.job_queue[0]

                # Check if job is still valid
                if job_id not in self.jobs:
                    self.job_queue.pop(0)
                    continue

                job = self.jobs[job_id]

                # Skip cancelled or completed jobs
                if job.status in [JobStatus.CANCELLED, JobStatus.COMPLETED, JobStatus.FAILED]:
                    self.job_queue.pop(0)
                    continue

                # Check if we can process this job (including intermediate states)
                if self._can_process_job(job):
                    self.job_queue.pop(0)
                    return job

                # Break to prevent busy waiting
                break

            return None

    def _can_process_job(self, job: BurnJob) -> bool:
        """Check if a job can be processed (started or continued)."""
        in_progress_statuses = [JobStatus.DOWNLOADING, JobStatus.BURNING, JobStatus.VERIFYING]
        active_jobs = len([j for j in self.jobs.values() if j.status in in_progress_statuses])

        # Allow processing if:
        # 1. We have capacity for active jobs, OR
        # 2. The job is not in an active state (intermediate states like DOWNLOADED, JDF_READY, etc.)
        return (
            active_jobs < app_config.max_concurrent_jobs or job.status not in in_progress_statuses
        )

    def start_job_processing(self, job: BurnJob):
        """Start processing a job."""
        try:
            # Check if job was cancelled before starting any processing
            if job.status == JobStatus.CANCELLED:
                self.logger.info(f"Skipping cancelled job {job.id}")
                return

            if job.status == JobStatus.PENDING:
                self._start_download(job)
            elif job.status == JobStatus.DOWNLOADED:
                self._start_jdf_generation(job)
            elif job.status == JobStatus.JDF_READY:
                self._queue_for_burning(job)
            elif job.status in [JobStatus.QUEUED_FOR_BURNING]:
                self._start_burning(job)

        except Exception as e:
            self.logger.error(f"Error processing job {job.id}: {e}")
            job.update_status(JobStatus.FAILED, str(e), job_queue=self)
            self._notify_job_update(job)

    def _start_download(self, job: BurnJob):
        """Start downloading ISO file."""
        # Check if job was cancelled before starting download
        if job.status == JobStatus.CANCELLED:
            self.logger.info(f"Skipping download for cancelled job {job.id}")
            return

        job.update_status(JobStatus.DOWNLOADING)
        self._notify_job_update(job)

        # Start download in background thread
        download_thread = threading.Thread(target=self._download_worker, args=(job,), daemon=True)
        download_thread.start()

    def _download_worker(self, job: BurnJob):
        """Worker function for downloading."""
        try:
            iso_path = self.download_manager.download_iso(job.iso_info)

            if iso_path:
                job.iso_path = iso_path

                # Detect disc type based on file size
                job.disc_type = job.detect_disc_type(iso_path, self)

                # Check if job was cancelled before updating status
                if job.status != JobStatus.CANCELLED:
                    job.update_status(JobStatus.DOWNLOADED)
                    self.logger.info(f"Downloaded ISO for job {job.id}")
            else:
                # Check if job was cancelled before marking as failed
                if job.status != JobStatus.CANCELLED:
                    job.update_status(JobStatus.FAILED, "Download failed", job_queue=self)
                    self.logger.error(f"Failed to download ISO for job {job.id}")

        except Exception as e:
            job.update_status(JobStatus.FAILED, str(e), job_queue=self)
            self.logger.error(f"Error in download worker for job {job.id}: {e}")
        finally:
            self._notify_job_update(job)

    def _on_download_progress(self, iso_id: str, progress):
        """Handle download progress updates."""
        try:
            # Find job by ISO ID
            for job in self.jobs.values():
                if job.iso_info.get("id") == iso_id and job.status == JobStatus.DOWNLOADING:
                    job.progress = progress.progress_percentage
                    job.updated_at = datetime.now()
                    self._notify_job_update(job)
                    break
        except Exception as e:
            self.logger.error(f"Error handling download progress for {iso_id}: {e}")

    def _start_jdf_generation(self, job: BurnJob):
        """Start JDF file generation."""
        # Check if job was cancelled before starting JDF generation
        if job.status == JobStatus.CANCELLED:
            self.logger.info(f"Skipping JDF generation for cancelled job {job.id}")
            return

        if not job.iso_path:
            if job.status != JobStatus.CANCELLED:
                job.update_status(JobStatus.FAILED, "No ISO file path", job_queue=self)
                self._notify_job_update(job)
            return

        if job.status != JobStatus.CANCELLED:
            job.update_status(JobStatus.GENERATING_JDF)
            self._notify_job_update(job)

        try:
            jdf_generator = JDFGenerator(job.id)
            jdf_path = jdf_generator.create_burn_job_jdf()

            job.jdf_path = jdf_path

            # Check if job was cancelled before updating status
            if job.status != JobStatus.CANCELLED:
                job.update_status(JobStatus.JDF_READY)
                self.logger.info(f"Generated JDF for job {job.id}")

        except Exception as e:
            # Check if job was cancelled before marking as failed
            if job.status != JobStatus.CANCELLED:
                job.update_status(
                    JobStatus.FAILED, f"JDF generation failed: {str(e)}", job_queue=self
                )
                self.logger.error(f"Failed to generate JDF for job {job.id}: {e}")
        finally:
            self._notify_job_update(job)

    def _queue_for_burning(self, job: BurnJob):
        """Queue job for burning."""
        # Check if job was cancelled before queuing for burning
        if job.status == JobStatus.CANCELLED:
            self.logger.info(f"Skipping queue for burning for cancelled job {job.id}")
            return

        if job.status != JobStatus.CANCELLED:
            job.update_status(JobStatus.QUEUED_FOR_BURNING)
            self._notify_job_update(job)

    def _start_burning(self, job: BurnJob):
        """Start burning process."""
        # Check if job was cancelled before starting burning
        if job.status == JobStatus.CANCELLED:
            self.logger.info(f"Skipping burning for cancelled job {job.id}")
            return

        if job.status != JobStatus.CANCELLED:
            job.update_status(JobStatus.BURNING)
            job.progress = 0.0
            self._notify_job_update(job)

        # In a real implementation, this would communicate with the robot
        # For now, we'll simulate the burning process
        burn_thread = threading.Thread(target=self._burn_loop, args=(job,), daemon=True)
        burn_thread.start()

    def _burn_loop(self, job: BurnJob):
        """Loop for burning simulation."""
        try:
            max_time = datetime.now() + timedelta(minutes=app_config.burner_timeout)
            while job.status == JobStatus.BURNING:
                if datetime.now() > max_time:
                    raise Exception("Burning timed out")

                self._check_burn_status(job)
                self._notify_job_update(job)
                time.sleep(10)  # wait 10 seconds before checking again

        except Exception as e:
            self.logger.error(f"Error in burn loop for job {job.id}")
            job.update_status(JobStatus.FAILED, str(e), job_queue=self)
            self._notify_job_update(job)

    def _check_burn_status(self, job: BurnJob):
        """Worker function for burning simulation."""
        jdf_handler = JDFHandler(job.jdf_path)
        try:
            if jdf_handler.status == JDFHandler.Status.SUCCESS:
                job.update_status(JobStatus.COMPLETED, job_queue=self)
                job.progress = 100.0

                self.logger.info(f"Completed job {job.id}")
                return

            if jdf_handler.status == JDFHandler.Status.PROCESSING:
                self.logger.info("Job in progress: %s", job.id)
                job.progress = 50.0
                return

            if jdf_handler.status == JDFHandler.Status.ERROR:
                raise Exception(f"Burner responded with error for job {job.id}")

        except Exception as e:
            job.update_status(JobStatus.FAILED, f"Burning failed: {str(e)}", job_queue=self)
            self.logger.error(f"Error in burn worker for job {job.id}: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if not found
        """
        with self.lock:
            if job_id not in self.jobs:
                return False

            job = self.jobs[job_id]

            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False

            # Check current status before changing it
            was_downloading = job.status == JobStatus.DOWNLOADING

            job.update_status(JobStatus.CANCELLED, "Cancelled by user", job_queue=self)

            # Remove from queue if present
            if job_id in self.job_queue:
                self.job_queue.remove(job_id)

            # Cancel active operations based on previous status
            if was_downloading:
                self.download_manager.cancel_download(job.iso_info.get("id"))

            self.logger.info(f"Cancelled job {job_id}")
            self._notify_job_update(job)
            return True

    def retry_job(self, job_id: str) -> bool:
        """Retry a failed or completed job.

        Args:
            job_id: Job ID to retry

        Returns:
            True if retried, False if cannot retry
        """
        with self.lock:
            if job_id not in self.jobs:
                return False

            job = self.jobs[job_id]

            # Clean up existing files to start fresh
            self._cleanup_job_files(job)

            job.update_status(JobStatus.PENDING)
            job.error_message = None
            job.progress = 0.0
            job.notification_sent = False

            # Clear file paths so they get regenerated
            job.iso_path = None
            job.jdf_path = None

            # Re-add to queue (at the end for retry)
            self.job_queue.append(job_id)

            self.logger.info(f"Retrying job {job_id} (attempt {job.retry_count})")
            self._notify_job_update(job)
            return True

    def _cleanup_job_files(self, job: BurnJob):
        """Clean up job files before retry."""
        try:
            # Remove ISO file if it exists
            if job.iso_path and Path(job.iso_path).exists():
                Path(job.iso_path).unlink()
                self.logger.debug(f"Removed ISO file: {job.iso_path}")

            # Remove JDF file if it exists
            if job.jdf_path and Path(job.jdf_path).exists():
                Path(job.jdf_path).unlink()
                self.logger.debug(f"Removed JDF file: {job.jdf_path}")

            # Remove done file if it exists
            done_files = self._get_wildcard_files(job.jdf_path, "DON")
            for done_file in done_files:
                Path(done_file).unlink()
                self.logger.debug(f"Removed done file: {done_file}")

            # Remove inp file if it exists
            inp_files = self._get_wildcard_files(job.jdf_path, "INP")
            for inp_file in inp_files:
                Path(inp_file).unlink()
                self.logger.debug(f"Removed inp file: {inp_file}")

            # Remove error file if it exists
            error_files = self._get_wildcard_files(job.jdf_path, "ERR")
            for error_file in error_files:
                Path(error_file).unlink()
                self.logger.debug(f"Removed error file: {error_file}")

        except Exception as e:
            self.logger.warning(f"Error cleaning up files for job {job.id}: {e}")

    def get_job(self, job_id: str) -> Optional[BurnJob]:
        """Get a specific job by ID."""
        return self.jobs.get(job_id)

    def get_jobs_by_status(self, status: JobStatus) -> List[BurnJob]:
        """Get all jobs with a specific status."""
        return [job for job in self.jobs.values() if job.status == status]

    def get_all_jobs(self) -> List[BurnJob]:
        """Get all jobs."""
        return list(self.jobs.values())

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self.lock:
            pending = len(self.get_jobs_by_status(JobStatus.PENDING))
            downloading = len(self.get_jobs_by_status(JobStatus.DOWNLOADING))
            burning = len(self.get_jobs_by_status(JobStatus.BURNING))
            completed = len(self.get_jobs_by_status(JobStatus.COMPLETED))
            failed = len(self.get_jobs_by_status(JobStatus.FAILED))

            return {
                "total_jobs": len(self.jobs),
                "pending": pending,
                "downloading": downloading,
                "burning": burning,
                "completed": completed,
                "failed": failed,
                "queue_length": len(self.job_queue),
                "active_slots": min(app_config.max_concurrent_jobs, downloading + burning),
            }

    def cleanup_completed_jobs(self, max_age_days: int = 7):
        """Clean up old completed jobs.

        Args:
            max_age_days: Maximum age in days before cleanup
        """
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)

        with self.lock:
            to_remove = []
            for job_id, job in self.jobs.items():
                if (
                    job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
                    and job.updated_at.timestamp() < cutoff_time
                ):
                    to_remove.append(job_id)

            for job_id in to_remove:
                del self.jobs[job_id]

            if to_remove:
                self.logger.info(f"Cleaned up {len(to_remove)} old jobs")
