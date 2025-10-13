"""
Job Queue Management for EPSON PP-100 Disc Burner Application
"""

import logging
import random
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from config import Config
from iso_downloader import ISODownloadManager
from jdf_generator import JDFGenerator


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


class JobPriority(Enum):
    """Job priority enumeration."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class BurnJob:
    """Represents a disc burning job."""

    id: str
    iso_info: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
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

    def update_status(self, status: JobStatus, error_message: Optional[str] = None):
        """Update job status and timestamp."""
        self.status = status
        self.updated_at = datetime.now()
        if error_message:
            self.error_message = error_message

    def can_retry(self, max_retries: int) -> bool:
        """Check if job can be retried."""
        return self.retry_count < max_retries and self.status == JobStatus.FAILED

    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.updated_at = datetime.now()


class JobQueue:
    """Thread-safe job queue for managing burning jobs."""

    def __init__(self, config: Config):
        """Initialize job queue.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Job storage
        self.jobs: Dict[str, BurnJob] = {}
        self.job_queue: List[str] = []  # Queue of job IDs by priority

        # Threading
        self.lock = threading.RLock()

        # Callbacks
        self.job_update_callbacks: List[Callable[[BurnJob], None]] = []

        # Components
        self.download_manager = ISODownloadManager(config)
        self.jdf_generator = JDFGenerator(config)

        # Setup progress callbacks
        self.download_manager.add_progress_callback(self._on_download_progress)

    def add_job_update_callback(self, callback: Callable[[BurnJob], None]):
        """Add callback for job updates."""
        self.job_update_callbacks.append(callback)

    def remove_job_update_callback(self, callback: Callable[[BurnJob], None]):
        """Remove job update callback."""
        if callback in self.job_update_callbacks:
            self.job_update_callbacks.remove(callback)

    def _notify_job_update(self, job: BurnJob):
        """Notify all callbacks of job update."""
        for callback in self.job_update_callbacks:
            try:
                callback(job)
            except Exception as e:
                self.logger.error(f"Error in job update callback: {e}")

    def add_job(self, iso_info: Dict[str, Any], priority: JobPriority = JobPriority.NORMAL) -> str:
        """Add a new job to the queue.

        Args:
            iso_info: ISO information from API
            priority: Job priority

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        with self.lock:
            job = BurnJob(id=job_id, iso_info=iso_info, priority=priority)

            self.jobs[job_id] = job

            # Add to queue based on priority
            self._insert_job_by_priority(job_id)

            self.logger.info(f"Added job {job_id} for ISO {iso_info.get('id', 'unknown')}")
            self._notify_job_update(job)

        return job_id

    def _insert_job_by_priority(self, job_id: str):
        """Insert job into queue based on priority."""
        job = self.jobs[job_id]
        priority_value = job.priority.value

        # Find insertion point
        insert_pos = 0
        for i, existing_job_id in enumerate(self.job_queue):
            existing_job = self.jobs[existing_job_id]
            if existing_job.priority.value < priority_value:
                insert_pos = i + 1
            else:
                insert_pos = i
                break

        self.job_queue.insert(insert_pos, job_id)

    def get_next_job(self) -> Optional[BurnJob]:
        """Get the next job to process."""
        with self.lock:
            while self.job_queue:
                job_id = self.job_queue[0]

                # Check if job is still valid
                if job_id not in self.jobs:
                    self.job_queue.pop(0)
                    continue

                job = self.jobs[job_id]

                # Skip cancelled or completed jobs
                if job.status in [JobStatus.CANCELLED, JobStatus.COMPLETED]:
                    self.job_queue.pop(0)
                    continue

                # Check if we can process this job (including intermediate states)
                if self._can_process_job(job):
                    self.job_queue.pop(0)
                    return job

            return None

    def _can_process_job(self, job: BurnJob) -> bool:
        """Check if a job can be processed (started or continued)."""
        # Check concurrent job limit - only count truly active jobs
        active_jobs = len(
            [
                j
                for j in self.jobs.values()
                if j.status in [JobStatus.DOWNLOADING, JobStatus.BURNING, JobStatus.VERIFYING]
            ]
        )

        # Allow processing if:
        # 1. We have capacity for active jobs, OR
        # 2. The job is not in an active state (intermediate states like DOWNLOADED, JDF_READY, etc.)
        return active_jobs < self.config.max_concurrent_jobs or job.status not in [
            JobStatus.DOWNLOADING,
            JobStatus.BURNING,
            JobStatus.VERIFYING,
        ]

    def start_job_processing(self, job: BurnJob):
        """Start processing a job."""
        try:
            if job.status == JobStatus.PENDING:
                self._start_download(job)
            elif job.status == JobStatus.DOWNLOADED:
                self._start_jdf_generation(job)
            elif job.status == JobStatus.JDF_READY:
                self._queue_for_burning(job)
            elif job.status == JobStatus.QUEUED_FOR_BURNING:
                self._start_burning(job)

        except Exception as e:
            self.logger.error(f"Error processing job {job.id}: {e}")
            job.update_status(JobStatus.FAILED, str(e))
            self._notify_job_update(job)

    def _start_download(self, job: BurnJob):
        """Start downloading ISO file."""
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
                job.update_status(JobStatus.DOWNLOADED)
                self.logger.info(f"Downloaded ISO for job {job.id}")
            else:
                job.update_status(JobStatus.FAILED, "Download failed")
                self.logger.error(f"Failed to download ISO for job {job.id}")

        except Exception as e:
            job.update_status(JobStatus.FAILED, str(e))
            self.logger.error(f"Error in download worker for job {job.id}: {e}")
        finally:
            self._notify_job_update(job)

    def _on_download_progress(self, iso_id: str, progress):
        """Handle download progress updates."""
        # Find job by ISO ID
        for job in self.jobs.values():
            if job.iso_info.get("id") == iso_id and job.status == JobStatus.DOWNLOADING:
                job.progress = progress.progress_percentage
                job.updated_at = datetime.now()
                self._notify_job_update(job)
                break

    def _start_jdf_generation(self, job: BurnJob):
        """Start JDF file generation."""
        if not job.iso_path:
            job.update_status(JobStatus.FAILED, "No ISO file path")
            self._notify_job_update(job)
            return

        job.update_status(JobStatus.GENERATING_JDF)
        self._notify_job_update(job)

        try:
            jdf_path = self.jdf_generator.create_burn_job_jdf(
                job.iso_path,
                job.id,
                burn_speed=self.config.burn_speed,
                verify=self.config.verify_after_burn,
            )

            job.jdf_path = jdf_path
            job.update_status(JobStatus.JDF_READY)
            self.logger.info(f"Generated JDF for job {job.id}")

        except Exception as e:
            job.update_status(JobStatus.FAILED, f"JDF generation failed: {str(e)}")
            self.logger.error(f"Failed to generate JDF for job {job.id}: {e}")
        finally:
            self._notify_job_update(job)

    def _queue_for_burning(self, job: BurnJob):
        """Queue job for burning."""
        job.update_status(JobStatus.QUEUED_FOR_BURNING)
        self._notify_job_update(job)

        # In a real implementation, this would communicate with the robot
        # For now, we'll simulate the burning process
        burn_thread = threading.Thread(target=self._burn_worker, args=(job,), daemon=True)
        burn_thread.start()

    def _start_burning(self, job: BurnJob):
        """Start burning process."""
        job.update_status(JobStatus.BURNING)
        job.progress = 0.0
        self._notify_job_update(job)

    def _burn_worker(self, job: BurnJob):
        """Worker function for burning simulation."""
        try:
            # Simulate burning process

            # Simulate different burning phases
            phases = [
                ("Preparing disc", 10),
                ("Burning data", 70),
                ("Verifying", 15),
                ("Finalizing", 5),
            ]

            for phase_name, phase_progress in phases:
                time.sleep(random.uniform(1, 3))  # Simulate time

                if job.status == JobStatus.CANCELLED:
                    return

                job.progress = phase_progress
                self._notify_job_update(job)

            # Simulate verification if enabled
            if self.config.verify_after_burn:
                job.update_status(JobStatus.VERIFYING)
                job.progress = 85
                self._notify_job_update(job)

                time.sleep(random.uniform(2, 4))

                if job.status == JobStatus.CANCELLED:
                    return

            # Complete the job
            job.update_status(JobStatus.COMPLETED)
            job.progress = 100.0

            # Move files to completed folder
            self._move_completed_files(job)

            self.logger.info(f"Completed job {job.id}")

        except Exception as e:
            job.update_status(JobStatus.FAILED, f"Burning failed: {str(e)}")
            self.logger.error(f"Error in burn worker for job {job.id}: {e}")
        finally:
            self._notify_job_update(job)

    def _move_completed_files(self, job: BurnJob):
        """Move completed job files to completed folder."""
        try:
            if job.iso_path:

                completed_iso = self.config.completed_folder / Path(job.iso_path).name
                shutil.move(job.iso_path, completed_iso)

            if job.jdf_path:
                completed_jdf = self.config.completed_folder / Path(job.jdf_path).name

                shutil.move(job.jdf_path, completed_jdf)

        except Exception as e:
            self.logger.error(f"Error moving completed files for job {job.id}: {e}")

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

            job.update_status(JobStatus.CANCELLED, "Cancelled by user")

            # Remove from queue if present
            if job_id in self.job_queue:
                self.job_queue.remove(job_id)

            # Cancel download if active
            if job.status == JobStatus.DOWNLOADING:
                self.download_manager.cancel_download(job.iso_info.get("id"))

            self.logger.info(f"Cancelled job {job_id}")
            self._notify_job_update(job)
            return True

    def retry_job(self, job_id: str) -> bool:
        """Retry a failed job.

        Args:
            job_id: Job ID to retry

        Returns:
            True if retried, False if cannot retry
        """
        with self.lock:
            if job_id not in self.jobs:
                return False

            job = self.jobs[job_id]

            if not job.can_retry(self.config.max_retries):
                return False

            job.increment_retry()
            job.update_status(JobStatus.PENDING)
            job.error_message = None
            job.progress = 0.0

            # Re-add to queue
            self._insert_job_by_priority(job_id)

            self.logger.info(f"Retrying job {job_id} (attempt {job.retry_count})")
            self._notify_job_update(job)
            return True

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
                "active_slots": min(self.config.max_concurrent_jobs, downloading + burning),
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
