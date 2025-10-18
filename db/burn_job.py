"""
Database Service Layer for Burn Job Management

This module provides the data access layer for managing burn job records in the SQLite database.
Implements the Repository pattern with static methods for clean separation of concerns.

Architecture:
    - Service layer: Business logic for job operations
    - Model layer: SQLAlchemy ORM models
    - Engine layer: Database connection and session management

Features:
    - CRUD operations for burn job records
    - DICOM study information management
    - Automatic session lifecycle management
    - Error handling and logging
    - Database statistics and cleanup operations

Thread Safety:
    - All operations use context managers for automatic session management
    - No shared mutable state between threads
    - Session-scoped operations ensure data consistency
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.engine import SessionLocal
from db.models.burn_job import BurnJobRecord

logger = logging.getLogger(__name__)


def with_session(func):
    """Decorator for automatic session management."""

    def execute_func(*args, session: Session = None, **kwargs):
        commit = kwargs.pop("commit", False)
        result = func(*args, **kwargs, session=session)
        if commit:
            session.commit()
        return result

    def wrapper(*args, **kwargs):
        session = kwargs.pop("session", None)
        if session:
            return execute_func(*args, session=session, **kwargs)

        with SessionLocal() as session:
            return execute_func(*args, session=session, **kwargs)

    return wrapper


def save_job(
    job_id: str, iso_info: Dict[str, Any], session: Session = None, **kwargs
) -> BurnJobRecord:
    """Save or update a job record.

    Args:
        job_id: Job ID
        iso_info: ISO information
        **kwargs: Additional job fields

    Returns:
        Created/updated job record
    """
    try:
        # Check if job already exists
        existing = session.query(BurnJobRecord).filter_by(id=job_id).first()

        if existing:
            # Update existing record
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()

            # Update DICOM study fields if provided
            if "study" in iso_info:
                study = iso_info["study"]
                patient = study.get("patient", {})

                if hasattr(existing, "study_patient_name"):
                    existing.study_patient_name = patient.get("fullName")
                if hasattr(existing, "study_patient_id"):
                    existing.study_patient_id = patient.get("identifier")
                if hasattr(existing, "study_patient_birth_date"):
                    existing.study_patient_birth_date = patient.get("birthDate")
                if hasattr(existing, "study_dicom_date_time"):
                    existing.study_dicom_date_time = study.get("dicomDateTime")
                if hasattr(existing, "study_dicom_description"):
                    existing.study_dicom_description = study.get("dicomDescription")

            record = existing
        else:
            # Create new record
            record = BurnJobRecord.from_job_data(job_id, iso_info, **kwargs)
            session.add(record)

        return record

    except SQLAlchemyError as e:
        logger.error(f"Error saving job {job_id}: {e}")
        raise


class BurnJob:
    """
    Service class for managing burn job records in the database.

    This class implements the Repository pattern, providing a clean API for
    all database operations related to burn jobs. All methods are static
    to ensure thread safety and avoid state management complexity.

    Database Operations:
        - save_job(): Create or update job records
        - get_all_jobs(): Retrieve all jobs with optional filtering
        - get_job(): Retrieve specific job by ID
        - update_job_state(): Update job status and progress
        - delete_job(): Remove job from database
        - cleanup_old_jobs(): Remove old completed/failed jobs
        - get_storage_stats(): Get database statistics

    DICOM Integration:
        - Automatic extraction of patient and study information
        - Mapping between GraphQL API response and database schema
        - Support for all DICOM study fields (patient, dates, descriptions)

    Error Handling:
        - SQLAlchemy exceptions are caught and logged
        - Graceful degradation with empty results on errors
        - Comprehensive error logging for debugging
    """

    @staticmethod
    @with_session
    def save_job(
        job_id: str, iso_info: Dict[str, Any], session: Session = None, **kwargs
    ) -> BurnJobRecord:
        """Save or update a job record.

        Args:
            job_id: Job ID
            iso_info: ISO information
            **kwargs: Additional job fields
        """
        return save_job(job_id, iso_info, session=session, **kwargs)

    @staticmethod
    @with_session
    def get_all_jobs(session: Session = None) -> List[BurnJobRecord]:
        """Get all job records.

        Returns:
            List of all job records
        """
        try:
            return session.query(BurnJobRecord).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all jobs: {e}")
            return []

    @staticmethod
    @with_session
    def get_job(job_id: str, session: Session = None) -> Optional[BurnJobRecord]:
        """Get a job record by ID.

        Args:
            job_id: Job ID

        Returns:
            Job record or None if not found
        """
        try:
            return session.query(BurnJobRecord).filter_by(id=job_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None

    @staticmethod
    @with_session
    def get_jobs_by_status(status: str, session: Session = None) -> List[BurnJobRecord]:
        """Get jobs by status.

        Args:
            status: Job status

        Returns:
            List of jobs with specified status
        """
        try:
            return session.query(BurnJobRecord).filter_by(status=status).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting jobs by status {status}: {e}")
            return []

    @staticmethod
    @with_session
    def update_job_state(job, session: Session = None, **kwargs) -> bool:
        """
        Update job status and related fields in the database.

        This method synchronizes the in-memory job object with the database record,
        updating status, progress, file paths, error messages, and timestamps.
        It's called whenever a job's state changes during processing.

        Args:
            job: BurnJob instance containing updated status and metadata
            session: Optional SQLAlchemy session (auto-managed if not provided)
            **kwargs: Additional arguments for the update

        Returns:
            bool: True if update was successful, False if job not found or error occurred

        Updated Fields:
        - status: Current job status (PENDING, DOWNLOADING, etc.)
        - progress: Numeric progress percentage (0.0 to 100.0)
        - iso_path: Path to downloaded ISO file
        - jdf_path: Path to generated JDF file
        - error_message: Error description if job failed
        - disc_type: Detected disc type (CD/DVD)
        - updated_at: Timestamp of last update

        Error Handling:
        - Returns False if job record not found in database
        - Logs SQLAlchemy errors but doesn't raise them
        - Ensures atomic updates within session transaction

        Thread Safety:
        - Session management ensures thread-safe database operations
        - Multiple concurrent updates to different jobs are supported
        """
        try:
            job_record = session.query(BurnJobRecord).filter_by(id=job.id).first()
            if not job_record:
                return False

            job_record.status = job.status.value
            job_record.progress = job.progress
            job_record.iso_path = job.iso_path
            job_record.jdf_path = job.jdf_path
            job_record.error_message = job.error_message
            job_record.disc_type = job.disc_type
            job_record.updated_at = datetime.utcnow()

            return True

        except SQLAlchemyError as e:
            logger.error(f"Error updating job status {job.id}: {e}")
            return False

    @staticmethod
    @with_session
    def delete_job(job_id: str, session: Session = None) -> bool:
        """
        Permanently remove a job record from the database.

        This method performs a hard delete of the specified job record.
        Use with caution as this operation cannot be undone and removes
        all historical data about the job.

        Args:
            job_id: Unique identifier of the job to delete
            session: Optional SQLAlchemy session (auto-managed if not provided)

        Returns:
            bool: True if job was found and deleted, False if job not found

        Warning:
        - This is a destructive operation that cannot be reversed
        - Consider using job status updates instead of deletion for auditing
        - Deleted jobs cannot be recovered from backups if needed

        Error Handling:
        - Returns False if job_id not found in database
        - Logs SQLAlchemy errors but doesn't raise them
        - Ensures atomic deletion within session transaction

        Use Cases:
        - Removing duplicate job entries
        - Cleaning up test data
        - Administrative job removal (with proper authorization)
        """
        try:
            job = session.query(BurnJobRecord).filter_by(id=job_id).first()
            if not job:
                return False

            session.delete(job)
            return True

        except SQLAlchemyError as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False

    @staticmethod
    @with_session
    def cleanup_old_jobs(max_age_days: int = 30, session: Session = None) -> int:
        """Clean up old completed and failed jobs.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of jobs deleted
        """
        try:
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - max_age_days)

            deleted_jobs = (
                session.query(BurnJobRecord)
                .filter(
                    BurnJobRecord.updated_at < cutoff_date,
                    BurnJobRecord.status.in_(["completed", "failed"]),
                )
                .delete(synchronize_session=False)
            )

            logger.info(f"Cleaned up {deleted_jobs} old jobs")
            return deleted_jobs

        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old jobs: {e}")
            return 0

    @staticmethod
    @with_session
    def get_storage_stats(session: Session = None) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        try:
            total_jobs = session.query(BurnJobRecord).count()
            pending_jobs = session.query(BurnJobRecord).filter_by(status="pending").count()
            completed_jobs = session.query(BurnJobRecord).filter_by(status="completed").count()
            failed_jobs = session.query(BurnJobRecord).filter_by(status="failed").count()

            return {
                "total_jobs": total_jobs,
                "pending_jobs": pending_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
            }
        except SQLAlchemyError as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}
