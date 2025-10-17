"""
Configuration management for EPSON PP-100 Disc Burner Application
"""

import os
from functools import wraps
from pathlib import Path
from typing import Any

import yaml


def safe_config_get(default_value: Any):
    """Decorator for config properties that provides a fallback default value.

    This decorator catches KeyError and other exceptions when accessing
    configuration values that may not exist in older config files, and
    returns the specified default value instead.

    Args:
        default_value: The default value to return if the config key is missing

    Returns:
        The decorated property function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self):
            try:
                return func(self)
            except (KeyError, TypeError):
                # KeyError: key doesn't exist in config_data
                # TypeError: config_data is None or not a dict
                return default_value

        return wrapper

    return decorator


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_file=None):
        """Initialize configuration.

        Args:
            config_file (str): Path to configuration file. If None, uses default.
        """
        if config_file is None:
            # Look for config in application directory
            config_dir = self.get_app_config_folder()
            config_file = config_dir / "config.yaml"
            print(f"Using default config file: {config_file}")

        self.config_file = Path(config_file)
        self.config_data = self.load_config()

        if not self.config_file.exists():
            self.save_config()

    def get_app_config_folder(self) -> Path:
        """Get the configuration folder for the application."""
        app_name = "eden-epson-burner"
        home = Path.home()
        if os.name == "nt":  # Windows
            config_folder = home / "AppData" / "Roaming" / app_name
        elif os.name == "posix":  # macOS and Linux
            config_folder = home / f".{app_name}"
        else:
            raise OSError("Unsupported operating system")
        return config_folder

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
        config_dir = self.get_app_config_folder()

        return {
            "api": {
                "graphql_endpoint": "http://localhost:8000/graphql-middleware/",
                "api_key": "",
                "timeout": 30,
                "retry_attempts": 3,
            },
            "folders": {
                "downloads": str(config_dir / "downloads"),
                "jdf_files": str(config_dir / "jdf_files"),
                "completed": str(config_dir / "completed"),
                "failed": str(config_dir / "failed"),
                "temp": str(config_dir / "temp"),
            },
            "robot": {
                "jdf_template": str(config_dir / "templates/jdf_template.jdf"),
                "label_file": str(config_dir / "templates/default.tdd"),
                "data_template": str(config_dir / "templates/template.data"),
                "robot_uuid": "00000000-0000-0000-0000-000000000000",
            },
            "jobs": {
                "max_concurrent": 3,
                "check_interval": 30,  # seconds
                "retry_failed": True,
                "max_retries": 2,
                "burner_timeout": 10,  # minutes
            },
            "gui": {
                "refresh_interval": 5000,  # milliseconds
                "show_notifications": True,
            },
            "database": {"file": str(config_dir / "database/burner_jobs.db"), "backup_count": 5},
            "logging": {
                "level": "INFO",
                "file": str(config_dir / "burner.log"),
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
    def jdf_template(self):
        """JDF template file name."""
        return self.config_data["robot"]["jdf_template"]

    @property
    def label_file(self):
        """Label file (.tdd) for disc cover printing."""
        return self.config_data["robot"]["label_file"]

    @property
    def data_template(self):
        """Data template file for additional disc information."""
        return self.config_data["robot"]["data_template"]

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
    @safe_config_get(True)  # Default: True (retry failed jobs)
    def retry_failed_jobs(self):
        """Whether to retry failed jobs."""
        return self.config_data["jobs"]["retry_failed"]

    @property
    @safe_config_get(2)  # Default: 2 retries
    def max_retries(self):
        """Maximum number of retries for failed jobs."""
        return self.config_data["jobs"]["max_retries"]

    @property
    @safe_config_get(10)  # Default: 10 minutes
    def burner_timeout(self):
        """Timeout in minutes before marking a burn job as failed."""
        return self.config_data["jobs"]["burner_timeout"]

    # GUI Configuration
    @property
    def gui_refresh_interval(self):
        """GUI refresh interval in milliseconds."""
        return self.config_data["gui"]["refresh_interval"]

    @property
    @safe_config_get(True)  # Default: True
    def show_notifications(self):
        """Whether to show system notifications."""
        return self.config_data["gui"]["show_notifications"]

    # Database Configuration
    @property
    def database_file(self):
        """Database file path."""
        return Path(self.config_data["database"]["file"])

    @property
    @safe_config_get(5)  # Default: 5 backups
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
