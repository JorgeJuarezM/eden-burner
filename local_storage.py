"""
Local database storage for job states and history using SQLAlchemy
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import logging

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config import Config


Base = declarative_base()


class BurnJobRecord(Base):
    """Database model for burn job records."""
    __tablename__ = 'burn_jobs'

    id = Column(String, primary_key=True)
    iso_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    download_url = Column(String)
    checksum = Column(String)
    priority = Column(Integer, default=2)  # JobPriority.NORMAL.value
    status = Column(String, default='pending')
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

    # Robot interaction
    robot_job_id = Column(String)
    estimated_completion = Column(DateTime)

    # Additional metadata
    description = Column(Text)
    project_id = Column(String)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            'id': self.id,
            'iso_id': self.iso_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'download_url': self.download_url,
            'checksum': self.checksum,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'iso_path': self.iso_path,
            'jdf_path': self.jdf_path,
            'progress': self.progress,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'robot_job_id': self.robot_job_id,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'description': self.description,
            'project_id': self.project_id
        }

    @classmethod
    def from_job_data(cls, job_id: str, iso_info: Dict[str, Any], **kwargs) -> 'BurnJobRecord':
        """Create record from job data."""
        return cls(
            id=job_id,
            iso_id=iso_info.get('id', ''),
            filename=iso_info.get('filename', ''),
            file_size=iso_info.get('fileSize'),
            download_url=iso_info.get('downloadUrl'),
            checksum=iso_info.get('checksum'),
            description=iso_info.get('description'),
            project_id=iso_info.get('projectId'),
            **kwargs
        )


class JobHistoryRecord(Base):
    """Database model for job history records."""
    __tablename__ = 'job_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message = Column(Text)
    error = Column(Boolean, default=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'message': self.message,
            'error': self.error
        }


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
        db_url = f'sqlite:///{self.config.database_file}'
        self.engine = create_engine(db_url, echo=False)

        # Create tables
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

    def update_job_status(self, job_id: str, status: str, error_message: str = None,
                         progress: float = None) -> bool:
        """Update job status and optionally error message and progress.

        Args:
            job_id: Job ID
            status: New status
            error_message: Error message if any
            progress: Progress percentage

        Returns:
            True if updated successfully
        """
        try:
            with self.get_session() as session:
                job = session.query(BurnJobRecord).filter_by(id=job_id).first()
                if not job:
                    return False

                job.status = status
                job.updated_at = datetime.utcnow()

                if error_message is not None:
                    job.error_message = error_message

                if progress is not None:
                    job.progress = progress

                session.commit()
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Error updating job status {job_id}: {e}")
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

                # Also delete history records
                session.query(JobHistoryRecord).filter_by(job_id=job_id).delete()

                session.delete(job)
                session.commit()
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting job {job_id}: {e}")
            return False

    def add_history_record(self, job_id: str, status: str, message: str = None,
                          error: bool = False) -> bool:
        """Add a history record for a job.

        Args:
            job_id: Job ID
            status: Job status
            message: Optional message
            error: Whether this is an error record

        Returns:
            True if added successfully
        """
        try:
            with self.get_session() as session:
                history = JobHistoryRecord(
                    job_id=job_id,
                    status=status,
                    message=message,
                    error=error
                )
                session.add(history)
                session.commit()
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Error adding history record for job {job_id}: {e}")
            return False

    def get_job_history(self, job_id: str) -> List[JobHistoryRecord]:
        """Get history records for a job.

        Args:
            job_id: Job ID

        Returns:
            List of history records
        """
        try:
            with self.get_session() as session:
                return session.query(JobHistoryRecord).filter_by(job_id=job_id).order_by(JobHistoryRecord.timestamp).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting history for job {job_id}: {e}")
            return []

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
                # Delete old history records first
                deleted_history = session.query(JobHistoryRecord).join(BurnJobRecord).filter(
                    BurnJobRecord.updated_at < cutoff_date,
                    BurnJobRecord.status.in_(['completed', 'failed'])
                ).delete(synchronize_session=False)

                # Delete old jobs
                deleted_jobs = session.query(BurnJobRecord).filter(
                    BurnJobRecord.updated_at < cutoff_date,
                    BurnJobRecord.status.in_(['completed', 'failed'])
                ).delete(synchronize_session=False)

                session.commit()

                self.logger.info(f"Cleaned up {deleted_jobs} old jobs and {deleted_history} history records")
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
                pending_jobs = session.query(BurnJobRecord).filter_by(status='pending').count()
                completed_jobs = session.query(BurnJobRecord).filter_by(status='completed').count()
                failed_jobs = session.query(BurnJobRecord).filter_by(status='failed').count()
                total_history = session.query(JobHistoryRecord).count()

                return {
                    'total_jobs': total_jobs,
                    'pending_jobs': pending_jobs,
                    'completed_jobs': completed_jobs,
                    'failed_jobs': failed_jobs,
                    'total_history_records': total_history,
                    'database_size_mb': self._get_database_size()
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
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.config.database_file.with_suffix(f'.backup_{timestamp}')

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
            backup_pattern = self.config.database_file.stem + '.backup_*'
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

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, default=str)

            self.logger.info(f"Exported {len(jobs)} jobs to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting jobs to JSON: {e}")
            return False
