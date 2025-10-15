"""
JDF (Job Definition Format) file generator for EPSON PP-100 robot
"""

import logging
import os

from jinja2 import Template

from config import Config


class JDFGenerator:
    """Generator for JDF files for EPSON PP-100 disc burning robot."""

    def __init__(self, config: Config, job_id: str):
        """Initialize JDF generator.

        Args:
            config: Application configuration
        """
        from app.local_storage import LocalStorage

        self.config = config
        self.logger = logging.getLogger(__name__)
        self.storage = LocalStorage(config)

        self.job_id = job_id
        self.job_data = self.storage.get_job(job_id)

    def _read_file_template(self, template_path: str) -> str:
        """Read a file template.

        Args:
            template_path: Path to the template file
        """
        if not template_path:
            raise ValueError("Template path is required")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, path: str, content: str):
        """Write content to a file.

        Args:
            path: Path to the file
            content: Content to write to the file
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _create_data_file(self) -> str:
        """Create a data file (.data) for additional disc information from template.

        Args:
            job_id: Unique job identifier

        Returns:
            Path to generated data file
        """
        # Ensure data folder exists (same as JDF folder for now)
        self.config.ensure_folders_exist()

        # Create data filename
        data_filename = f"{self.job_id}.data"
        data_path = self.config.jdf_folder / data_filename

        try:
            # Read data template
            template_content = self._read_file_template(self.config.data_template)

            patient_name = self.job_data.study_patient_name
            study_description = self.job_data.study_dicom_description
            study_date = (
                self.job_data.study_dicom_date_time.strftime("%Y-%m-%d")
                if self.job_data.study_dicom_date_time
                else ""
            )

            # Prepare template variables from job data and config
            template_vars = {
                "patient_name": patient_name,
                "study_description": study_description,
                "study_date": study_date,
            }

            # Render template with job data
            template = Template(template_content)
            data_content = template.render(**template_vars)

            # Write data file
            self._write_file(data_path, data_content)

            self.logger.info(f"Generated data file: {data_path}")
            return str(data_path)

        except Exception as e:
            self.logger.error(f"Error creating data file: {e}")
            raise

    def create_burn_job_jdf(self) -> str:
        """Create a JDF file for disc burning job.

        Args:
            iso_path: Path to the ISO file to burn
            job_id: Unique job identifier (generated if None)
            copies: Number of copies to burn

        Returns:
            Path to generated JDF file
        """
        # Ensure JDF folder exists
        self.config.ensure_folders_exist()

        # Create JDF filename
        jdf_filename = f"{self.job_id}.jdf"
        jdf_path = self.config.jdf_folder / jdf_filename

        try:
            # Generate data file (.data) for additional information
            data_path = self._create_data_file()

            # Read JDF template
            template_content = self._read_file_template(self.config.jdf_template)
            template = Template(template_content)

            patient_name = self.job_data.study_patient_name
            jdf_content = template.render(
                disc_type=self.job_data.disc_type,
                image=self.job_data.iso_path,
                volume_label=patient_name,
                label=self.config.label_file,
                replace_fields=data_path,
            )

            self._write_file(jdf_path, jdf_content)

            self.logger.info(f"Generated JDF file: {jdf_path}")
            return str(jdf_path)

        except Exception as e:
            self.logger.error(f"Error creating JDF file: {e}")
            raise
