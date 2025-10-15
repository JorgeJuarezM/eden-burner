"""
JDF (Job Definition Format) file generator for EPSON PP-100 robot
"""

import logging

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

            self.logger.info(f"Generated JDF file: {jdf_path}")
            return str(jdf_path)

        except Exception as e:
            self.logger.error(f"Error creating JDF file: {e}")
            raise
