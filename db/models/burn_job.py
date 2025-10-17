"""
Database model for burn job records
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from db.models.base import Base


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
