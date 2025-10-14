"""
Configuration management for EPSON PP-100 Disc Burner Application
"""

from pathlib import Path

import yaml


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_file=None):
        """Initialize configuration.

        Args:
            config_file (str): Path to configuration file. If None, uses default.
        """
        if config_file is None:
            # Look for config in application directory
            app_dir = Path(__file__).parent
            config_file = app_dir / "config.yaml"

        self.config_file = Path(config_file)
        self.config_data = self.load_config()

    def load_config(self):
        """Load configuration from file or create default."""
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            return self.get_default_config()

    def save_config(self):
        """Save current configuration to file."""
        # Ensure config directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(self.config_data, f, default_flow_style=False, indent=2)

    def get_default_config(self):
        """Get default configuration values."""
        app_dir = Path(__file__).parent.parent  # Go up one level to project root

        return {
            "api": {
                "graphql_endpoint": "https://api.example.com/graphql",
                "api_key": "",
                "timeout": 30,
                "retry_attempts": 3,
            },
            "folders": {
                "downloads": str(app_dir / "downloads"),
                "jdf_files": str(app_dir / "jdf_files"),
                "completed": str(app_dir / "completed"),
                "failed": str(app_dir / "failed"),
                "temp": str(app_dir / "temp"),
            },
            "robot": {
                "name": "EPSON_PP_100",
                "jdf_template": "default.jdf",
                "burn_speed": "8x",
                "verify_after_burn": True,
                "auto_eject": False,
                "robot_uuid": "00000000-0000-0000-0000-000000000000",
            },
            "jobs": {
                "max_concurrent": 3,
                "check_interval": 30,  # seconds
                "retry_failed": True,
                "max_retries": 2,
            },
            "gui": {
                "window_title": "EPSON PP-100 Disc Burner",
                "refresh_interval": 5000,  # milliseconds
                "show_notifications": True,
                "theme": "default",
            },
            "database": {"file": str(app_dir / "database/burner_jobs.db"), "backup_count": 5},
            "logging": {
                "level": "INFO",
                "file": str(app_dir / "logs/burner.log"),
                "max_size": 10 * 1024 * 1024,  # 10MB
                "backup_count": 5,
            },
        }

    # API Configuration
    @property
    def graphql_endpoint(self):
        """GraphQL API endpoint URL."""
        return self.config_data["api"]["graphql_endpoint"]

    @graphql_endpoint.setter
    def graphql_endpoint(self, value):
        self.config_data["api"]["graphql_endpoint"] = value

    @property
    def api_key(self):
        """API key for authentication."""
        return self.config_data["api"]["api_key"]

    @api_key.setter
    def api_key(self, value):
        self.config_data["api"]["api_key"] = value

    @property
    def api_timeout(self):
        """API request timeout in seconds."""
        return self.config_data["api"]["timeout"]

    # Folder Configuration
    @property
    def downloads_folder(self):
        """Folder for downloaded ISO files."""
        return Path(self.config_data["folders"]["downloads"])

    @property
    def jdf_folder(self):
        """Folder for JDF files."""
        return Path(self.config_data["folders"]["jdf_files"])

    @property
    def completed_folder(self):
        """Folder for completed jobs."""
        return Path(self.config_data["folders"]["completed"])

    @property
    def failed_folder(self):
        """Folder for failed jobs."""
        return Path(self.config_data["folders"]["failed"])

    @property
    def temp_folder(self):
        """Temporary folder for processing."""
        return Path(self.config_data["folders"]["temp"])

    # Robot Configuration
    @property
    def robot_uuid(self):
        """Robot UUID identifier."""
        return self.config_data["robot"]["robot_uuid"]

    @property
    def robot_name(self):
        """Robot name identifier."""
        return self.config_data["robot"]["name"]

    @property
    def jdf_template(self):
        """JDF template file name."""
        return self.config_data["robot"]["jdf_template"]

    @property
    def burn_speed(self):
        """Default burn speed."""
        return self.config_data["robot"]["burn_speed"]

    @property
    def verify_after_burn(self):
        """Whether to verify discs after burning."""
        return self.config_data["robot"]["verify_after_burn"]

    @property
    def auto_eject(self):
        """Whether to auto-eject discs after completion."""
        return self.config_data["robot"]["auto_eject"]

    # Job Configuration
    @property
    def max_concurrent_jobs(self):
        """Maximum number of concurrent burning jobs."""
        return self.config_data["jobs"]["max_concurrent"]

    @property
    def check_interval(self):
        """Interval for checking new ISOs (seconds)."""
        return self.config_data["jobs"]["check_interval"]

    @property
    def retry_failed_jobs(self):
        """Whether to retry failed jobs."""
        return self.config_data["jobs"]["retry_failed"]

    @property
    def max_retries(self):
        """Maximum number of retries for failed jobs."""
        return self.config_data["jobs"]["max_retries"]

    # GUI Configuration
    @property
    def window_title(self):
        """Main window title."""
        return self.config_data["gui"]["window_title"]

    @property
    def gui_refresh_interval(self):
        """GUI refresh interval in milliseconds."""
        return self.config_data["gui"]["refresh_interval"]

    @property
    def show_notifications(self):
        """Whether to show system notifications."""
        return self.config_data["gui"]["show_notifications"]

    # Database Configuration
    @property
    def database_file(self):
        """Database file path."""
        return Path(self.config_data["database"]["file"])

    @property
    def database_backup_count(self):
        """Number of database backups to keep."""
        return self.config_data["database"]["backup_count"]

    def ensure_folders_exist(self):
        """Create all required folders if they don't exist."""
        folders = [
            self.downloads_folder,
            self.jdf_folder,
            self.completed_folder,
            self.failed_folder,
            self.temp_folder,
        ]

        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

    def validate_config(self):
        """Validate configuration values."""
        errors = []

        # Validate API configuration
        if not self.graphql_endpoint.startswith(("http://", "https://")):
            errors.append("GraphQL endpoint must be a valid HTTP/HTTPS URL")

        # Validate folder paths
        if not self.downloads_folder.parent.exists():
            errors.append(
                f"Downloads folder parent directory does not exist: {self.downloads_folder.parent}"
            )

        # Validate job configuration
        if self.max_concurrent_jobs < 1:
            errors.append("Maximum concurrent jobs must be at least 1")

        if self.check_interval < 10:
            errors.append("Check interval must be at least 10 seconds")

        return errors
