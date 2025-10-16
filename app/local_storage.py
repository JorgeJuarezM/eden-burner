"""
Local database storage for job states and history using SQLAlchemy
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from config import Config
from app.job_queue import BurnJob

Base = declarative_base()


class BurnJobRecord(Base):
    """Database model for burn job records."""

    __tablename__ = "burn_jobs"

    id = Column(String, primary_key=True)
    iso_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)  # Derived from study info
    file_size = Column(Integer)  # Will be determined from actual file
    download_url = Column(String, nullable=False)  # From fileUrl
    checksum = Column(String)  # Not provided by current API
    priority = Column(Integer, default=2)  # JobPriority.NORMAL.value
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # File paths
    iso_path = Column(String)
    jdf_path = Column(String)

    # Progress tracking
    progress = Column(Float, default=0.0)
    error_message = Column(Text)

    # Retry tracking
    retry_count = Column(Integer, default=0)

    # Disc type detection
    disc_type = Column(String)  # "CD", "DVD", or None

    # Robot interaction
    robot_job_id = Column(String)
    estimated_completion = Column(DateTime)

    # DICOM Study information (from GraphQL API)
    study_patient_name = Column(String)  # study.patient.fullName
    study_patient_id = Column(String)  # study.patient.identifier
    study_patient_birth_date = Column(DateTime)  # study.patient.birthDate
    study_dicom_date_time = Column(DateTime)  # study.dicomDateTime
    study_dicom_description = Column(Text)  # study.dicomDescription

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            "id": self.id,
            "iso_id": self.iso_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "download_url": self.download_url,
            "checksum": self.checksum,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "iso_path": self.iso_path,
            "jdf_path": self.jdf_path,
            "progress": self.progress,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "disc_type": self.disc_type,
            "robot_job_id": self.robot_job_id,
            "estimated_completion": (
                self.estimated_completion.isoformat() if self.estimated_completion else None
            ),
            "study_patient_name": self.study_patient_name,
            "study_patient_id": self.study_patient_id,
            "study_patient_birth_date": (
                self.study_patient_birth_date.isoformat() if self.study_patient_birth_date else None
            ),
            "study_dicom_date_time": (
                self.study_dicom_date_time.isoformat() if self.study_dicom_date_time else None
            ),
            "study_dicom_description": self.study_dicom_description,
        }

    @classmethod
    def from_job_data(cls, job_id: str, iso_info: Dict[str, Any], **kwargs) -> "BurnJobRecord":
        """Create record from job data matching GraphQL API response."""
        # Extract study information
        study = iso_info.get("study", {})
        patient = study.get("patient", {})

        # Generate filename from study info
        patient_name = patient.get("fullName", "Unknown")
        dicom_date = study.get("dicomDateTime", "")
        filename = (
            f"{patient_name}_{dicom_date}".replace(" ", "_").replace(":", "")
            if dicom_date
            else f"{patient_name}_study"
        )

        # Handle backward compatibility with old data format
        old_filename = iso_info.get("filename")
        if old_filename and not filename.startswith("Unknown"):
            filename = old_filename

        # Convert string dates to datetime objects for SQLAlchemy
        def parse_datetime(date_str):
            if isinstance(date_str, str):
                try:
                    from datetime import datetime

                    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    return None
            return date_str

        return cls(
            id=job_id,
            iso_id=iso_info.get("id", ""),
            filename=filename,
            file_size=iso_info.get("fileSize"),
            download_url=iso_info.get("fileUrl") or iso_info.get("downloadUrl", ""),
            checksum=iso_info.get("checksum"),
            study_patient_name=patient.get("fullName"),
            study_patient_id=patient.get("identifier"),
            study_patient_birth_date=parse_datetime(patient.get("birthDate")),
            study_dicom_date_time=parse_datetime(study.get("dicomDateTime")),
            study_dicom_description=study.get("dicomDescription"),
            **kwargs,
        )


class LocalStorage:
    """Local database storage manager."""

    def __init__(self, config: Config):
        """Initialize local storage.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Create database directory if it doesn't exist
        db_dir = self.config.database_file.parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Create database engine
        db_url = f"sqlite:///{self.config.database_file}"

        self.logger.info(f"Using database: {db_url}")
        self.engine = create_engine(db_url, echo=False)

        # Create tables (will be no-op if they already exist)
        Base.metadata.create_all(self.engine)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def save_job(self, job_id: str, iso_info: Dict[str, Any], **kwargs) -> BurnJobRecord:
        """Save or update a job record.

        Args:
            job_id: Job ID
            iso_info: ISO information
            **kwargs: Additional job fields

        Returns:
            Created/updated job record
        """
        try:
            with self.get_session() as session:
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

                session.commit()
                return record

        except SQLAlchemyError as e:
            self.logger.error(f"Error saving job {job_id}: {e}")
            raise

    def get_job(self, job_id: str) -> Optional[BurnJobRecord]:
        """Get a job record by ID.

        Args:
            job_id: Job ID

        Returns:
            Job record or None if not found
        """
        try:
            with self.get_session() as session:
                return session.query(BurnJobRecord).filter_by(id=job_id).first()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting job {job_id}: {e}")
            return None

    def get_all_jobs(self) -> List[BurnJobRecord]:
        """Get all job records.

        Returns:
            List of all job records
        """
        try:
            with self.get_session() as session:
                return session.query(BurnJobRecord).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting all jobs: {e}")
            return []

    def get_jobs_by_status(self, status: str) -> List[BurnJobRecord]:
        """Get jobs by status.

        Args:
            status: Job status

        Returns:
            List of jobs with specified status
        """
        try:
            with self.get_session() as session:
                return session.query(BurnJobRecord).filter_by(status=status).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting jobs by status {status}: {e}")
            return []

    def update_job_state(self, job: BurnJob) -> bool:
        """Update job status and optionally error message and progress.

        Args:
            job: Job to update

        Returns:
            True if updated successfully
        """
        try:
            with self.get_session() as session:
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

                session.commit()
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Error updating job status {job.id}: {e}")
            return False

    def delete_job(self, job_id: str) -> bool:
        """Delete a job record.

        Args:
            job_id: Job ID

        Returns:
            True if deleted successfully
        """
        try:
            with self.get_session() as session:
                job = session.query(BurnJobRecord).filter_by(id=job_id).first()
                if not job:
                    return False

                session.delete(job)
                session.commit()
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting job {job_id}: {e}")
            return False

    def cleanup_old_jobs(self, max_age_days: int = 30) -> int:
        """Clean up old completed and failed jobs.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of jobs deleted
        """
        try:
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - max_age_days)

            with self.get_session() as session:
                # Delete old jobs
                deleted_jobs = (
                    session.query(BurnJobRecord)
                    .filter(
                        BurnJobRecord.updated_at < cutoff_date,
                        BurnJobRecord.status.in_(["completed", "failed"]),
                    )
                    .delete(synchronize_session=False)
                )

                session.commit()

                self.logger.info(f"Cleaned up {deleted_jobs} old jobs")
                return deleted_jobs

        except SQLAlchemyError as e:
            self.logger.error(f"Error cleaning up old jobs: {e}")
            return 0

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        try:
            with self.get_session() as session:
                total_jobs = session.query(BurnJobRecord).count()
                pending_jobs = session.query(BurnJobRecord).filter_by(status="pending").count()
                completed_jobs = session.query(BurnJobRecord).filter_by(status="completed").count()
                failed_jobs = session.query(BurnJobRecord).filter_by(status="failed").count()

                return {
                    "total_jobs": total_jobs,
                    "pending_jobs": pending_jobs,
                    "completed_jobs": completed_jobs,
                    "failed_jobs": failed_jobs,
                    "database_size_mb": self._get_database_size(),
                }

        except SQLAlchemyError as e:
            self.logger.error(f"Error getting storage stats: {e}")
            return {}

    def _get_database_size(self) -> float:
        """Get database file size in MB."""
        try:
            if self.config.database_file.exists():
                size_bytes = self.config.database_file.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
            return 0.0
        except Exception:
            return 0.0

    def backup_database(self) -> Optional[str]:
        """Create a backup of the database.

        Returns:
            Path to backup file or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.config.database_file.with_suffix(f".backup_{timestamp}")

            # Simple file copy backup
            import shutil

            shutil.copy2(self.config.database_file, backup_path)

            self.logger.info(f"Created database backup: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Error creating database backup: {e}")
            return None

    def cleanup_old_backups(self, keep_count: int = None) -> int:
        """Clean up old database backups.

        Args:
            keep_count: Number of backups to keep (uses config value if None)

        Returns:
            Number of backups deleted
        """
        if keep_count is None:
            keep_count = self.config.database_backup_count

        try:
            backup_pattern = self.config.database_file.stem + ".backup_*"
            backup_files = list(self.config.database_file.parent.glob(backup_pattern))

            if len(backup_files) <= keep_count:
                return 0

            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda x: x.stat().st_mtime)

            # Delete old backups
            to_delete = backup_files[:-keep_count]
            for backup_file in to_delete:
                backup_file.unlink()
                self.logger.debug(f"Deleted old backup: {backup_file}")

            return len(to_delete)

        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")
            return 0

    def export_jobs_to_json(self, output_path: str) -> bool:
        """Export all jobs to JSON file.

        Args:
            output_path: Path to export file

        Returns:
            True if exported successfully
        """
        try:
            jobs = self.get_all_jobs()
            job_data = [job.to_dict() for job in jobs]

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(job_data, f, indent=2, default=str)

            self.logger.info(f"Exported {len(jobs)} jobs to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting jobs to JSON: {e}")
            return False

    def clear_database(self) -> bool:
        """Clear all data from the database (drop all tables and recreate them).

        Returns:
            True if cleared successfully
        """
        try:
            # Drop all tables
            Base.metadata.drop_all(self.engine)

            # Recreate all tables
            Base.metadata.create_all(self.engine)

            self.logger.info("Database cleared and recreated successfully")
            return True

        except SQLAlchemyError as e:
            self.logger.error(f"Error clearing database: {e}")
            return False
