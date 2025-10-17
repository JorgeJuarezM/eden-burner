"""
Local database storage for job states and history using SQLAlchemy
"""

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from config.config import Config
from db.models.base import Base

app_config = Config.get_current_config()


class LocalStorage:
    """Local database storage manager."""

    def __init__(self):
        """Initialize local storage.

        Args:
            config: Application configuration
        """
        self.logger = logging.getLogger(__name__)

        # Create database engine
        db_url = f"sqlite:///{app_config.database_file}"

        self.logger.info(f"Using database: {db_url}")
        self.engine = create_engine(db_url, echo=False)

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def ensure_database_directory(self):
        """Ensure the database directory exists."""
        db_dir = app_config.database_file.parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def migrate_database(self):
        """Create tables (will be no-op if they already exist)."""
        self.ensure_database_directory()

        # Create tables
        try:
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating tables: {e}")
            return False
        return True

    def _get_database_size(self) -> float:
        """Get database file size in MB."""
        try:
            if app_config.database_file.exists():
                size_bytes = app_config.database_file.stat().st_size
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
            backup_path = app_config.database_file.with_suffix(f".backup_{timestamp}")

            # Simple file copy backup
            import shutil

            shutil.copy2(app_config.database_file, backup_path)

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
            keep_count = app_config.database_backup_count

        try:
            backup_pattern = app_config.database_file.stem + ".backup_*"
            backup_files = list(app_config.database_file.parent.glob(backup_pattern))

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
