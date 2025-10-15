"""
JDF (Job Definition Format) file generator for EPSON PP-100 robot
"""

import logging
from datetime import datetime

from jinja2 import Template

from config import Config


class JDFGenerator:
    """Generator for JDF files for EPSON PP-100 disc burning robot."""

    def __init__(self, config: Config):
        """Initialize JDF generator.

        Args:
            config: Application configuration
        """
        from src.local_storage import LocalStorage

        self.config = config
        self.logger = logging.getLogger(__name__)
        self.storage = LocalStorage(config)

    def create_burn_job_jdf(
        self,
        job_id: str,
    ) -> str:
        """Create a JDF file for disc burning job.

        Args:
            iso_path: Path to the ISO file to burn
            job_id: Unique job identifier (generated if None)
            burn_speed: Burn speed (e.g., '8x', '16x')
            verify: Whether to verify after burning
            copies: Number of copies to burn

        Returns:
            Path to generated JDF file
        """
        # Ensure JDF folder exists
        self.config.ensure_folders_exist()

        job_data = self.storage.get_job(job_id)

        # Create JDF filename
        jdf_filename = f"{job_data.id}.jdf"
        jdf_path = self.config.jdf_folder / jdf_filename

        try:
            template_path = self.config.jdf_template
            with open(template_path, "r") as f:
                template_content = f.read()
            template = Template(template_content)

            patient_name = job_data.study_patient_name
            jdf_content = template.render(
                disc_type="DVD",
                image=job_data.iso_path,
                volume_label=patient_name,
                label=self.config.label_file,
                replace_fields="path/to/data_file.data",
            )

            with open(jdf_path, "w") as f:
                f.write(jdf_content)

            # Generate label file (.tdd) for disc cover
            try:
                label_path = self.create_label_file(job_id)
                self.logger.info(f"Generated label file: {label_path}")
            except Exception as e:
                self.logger.warning(f"Failed to generate label file: {e}")
                label_path = None

            # Generate data file (.data) for additional information
            try:
                data_path = self.create_data_file(job_id)
                self.logger.info(f"Generated data file: {data_path}")
            except Exception as e:
                self.logger.warning(f"Failed to generate data file: {e}")
                data_path = None

            self.logger.info(f"Generated JDF file: {jdf_path}")
            return str(jdf_path)

        except Exception as e:
            self.logger.error(f"Error creating JDF file: {e}")
            raise

    def create_label_file(self, job_id: str) -> str:
        """Create a label file (.tdd) for disc cover printing from template.

        Args:
            job_id: Unique job identifier

        Returns:
            Path to generated label file
        """
        # Ensure label folder exists (same as JDF folder for now)
        self.config.ensure_folders_exist()

        job_data = self.storage.get_job(job_id)

        # Create label filename
        label_filename = f"{job_data.id}.tdd"
        label_path = self.config.jdf_folder / label_filename

        try:
            # Read label template
            template_path = self.config.label_file
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Extract patient and study information from iso_info
            study_info = job_data.iso_info.get('study', {})
            patient_info = study_info.get('patient', {})
            patient_name = patient_info.get('fullName', 'Unknown Patient')
            study_description = study_info.get('description', '')

            # Prepare template variables from job data
            template_vars = {
                'job_id': job_id,
                'volume_label': patient_name,
                'label': f"JOB_{job_id}",
                'disc_type': 'DVD',
                'study_patient_name': patient_name,
                'study_date': job_data.created_at.strftime('%Y-%m-%d') if job_data.created_at else "",
                'study_description': study_description,
                'current_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            # Render template with job data
            template = Template(template_content)
            label_content = template.render(**template_vars)

            # Write label file
            with open(label_path, "w", encoding="utf-8") as f:
                f.write(label_content)

            self.logger.info(f"Generated label file: {label_path}")
            return str(label_path)

        except Exception as e:
            self.logger.error(f"Error creating label file: {e}")
            raise

    def create_data_file(self, job_id: str) -> str:
        """Create a data file (.data) for additional disc information from template.

        Args:
            job_id: Unique job identifier

        Returns:
            Path to generated data file
        """
        # Ensure data folder exists (same as JDF folder for now)
        self.config.ensure_folders_exist()

        job_data = self.storage.get_job(job_id)

        # Create data filename
        data_filename = f"{job_data.id}.data"
        data_path = self.config.jdf_folder / data_filename

        try:
            # Read data template
            template_path = self.config.data_template
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # Extract patient and study information from iso_info
            study_info = job_data.iso_info.get('study', {})
            patient_info = study_info.get('patient', {})
            patient_name = patient_info.get('fullName', 'Unknown Patient')
            study_description = study_info.get('description', '')

            # Prepare template variables from job data and config
            template_vars = {
                'job_id': job_id,
                'volume_label': patient_name,
                'label': f"JOB_{job_id}",
                'disc_type': 'DVD',
                'study_patient_name': patient_name,
                'patient_id': patient_info.get('identifier', ''),
                'study_date': job_data.created_at.strftime('%Y-%m-%d') if job_data.created_at else "",
                'study_description': study_description,
                'study_uid': study_info.get('uid', ''),
                'current_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'burn_speed': self.config.burn_speed,
                'verify_after_burn': str(self.config.verify_after_burn),
                'auto_eject': str(self.config.auto_eject),
                'robot_name': self.config.robot_name,
                'robot_uuid': self.config.robot_uuid,
                'iso_path': job_data.iso_path or '',
                'jdf_path': f"{job_data.id}.jdf",
                'label_path': f"{job_data.id}.tdd",
                'modality': study_info.get('modality', ''),
                'series_count': str(study_info.get('seriesCount', 0)),
                'image_count': str(study_info.get('imageCount', 0)),
                'replace_fields': 'path/to/data_file.data',
                'publisher': 'PP-100III',
                'copies': '1',
            }

            # Render template with job data
            template = Template(template_content)
            data_content = template.render(**template_vars)

            # Write data file
            with open(data_path, "w", encoding="utf-8") as f:
                f.write(data_content)

            self.logger.info(f"Generated data file: {data_path}")
            return str(data_path)

        except Exception as e:
            self.logger.error(f"Error creating data file: {e}")
            raise
