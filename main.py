#!/usr/bin/env python3
"""
EPSON PP-100 Disc Burner Application Launcher

This script serves as the main entry point for the application,
importing the actual implementation from the src/ directory.
"""
import argparse
import sys

from PyQt5.QtWidgets import QMessageBox
from filelock import FileLock, Timeout

# Import and run the main application
from app.main import EpsonBurnerApp
from config.config import Config

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="EPSON PP-100 Disc Burner Application")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run in background mode (system tray only, no GUI on startup)",
    )
    parser.add_argument("--test-config", action="store_true", help="Test configuration and exit")
    parser.add_argument("--clear-database", action="store_true", help="Clear the database and exit")

    args = parser.parse_args()

    if args.test_config:
        # Test configuration without starting GUI
        try:
            config = Config()
            config_errors = config.validate_config()
            if config_errors:
                print("Configuration errors found:")
                for error in config_errors:
                    print(f"  - {error}")
                return 1
            else:
                print("Configuration is valid")
                print(f"Robot UUID: {config.robot_uuid}")
                print(f"API Endpoint: {config.graphql_endpoint}")
                return 0
        except Exception as e:
            print(f"Error testing configuration: {e}")
            return 1

    if args.clear_database:
        # Clear the database
        try:
            from app.local_storage import LocalStorage

            storage = LocalStorage()
            success = storage.clear_database()
            if success:
                print("Database cleared successfully")
                return 0
            else:
                print("Error clearing database")
                return 1
        except Exception as e:
            print(f"Error clearing database: {e}")
            return 1

    # Default behavior: show GUI
    # Use --background flag to run in system tray only mode
    show_gui = not args.background

    try:
        burner_app = EpsonBurnerApp()
        with FileLock("app.lock", timeout=1):
            burner_app.initialize_application(show_gui=show_gui)
            return burner_app.run()
    except Timeout:
        print("Application already running")
        if show_gui:
            QMessageBox.warning(
                None,
                "Aplicación ya en ejecución",
                "La aplicación Eden Burner ya se está ejecutando.",
            )
        return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
