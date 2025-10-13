#!/usr/bin/env python3
"""
EPSON PP-100 Disc Burner Application

A PyQt5 application for managing ISO burning jobs with EPSON PP-100 robot.
Features:
- GraphQL API integration for ISO discovery
- Multi-task job queue management
- JDF file generation for robot communication
- Background execution support
- Intuitive GUI for job monitoring
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QMenu, QMessageBox,
                             QSystemTrayIcon)

import background_worker
import gui.main_window
import job_queue
import local_storage
from config import Config

# Import classes directly
JobQueue = job_queue.JobQueue
BurnJob = job_queue.BurnJob
JobStatus = job_queue.JobStatus
JobPriority = job_queue.JobPriority
MainWindow = gui.main_window.MainWindow
BackgroundWorker = background_worker.BackgroundWorker
LocalStorage = local_storage.LocalStorage


class EpsonBurnerApp:
    """Main application class for EPSON PP-100 disc burner management."""

    def __init__(self, show_gui=False):
        # Load configuration FIRST
        self.config = Config()

        # Setup logging (now that config is available)
        self.setup_logging()

        # Validate configuration
        config_errors = self.config.validate_config()
        if config_errors:
            self.show_config_errors(config_errors)
            return

        # Ensure folders exist
        self.config.ensure_folders_exist()

        # Initialize core components
        self.storage = LocalStorage(self.config)
        self.job_queue = JobQueue(self.config)
        self.background_worker = BackgroundWorker(self.config, self.job_queue)

        # Setup application
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Setup system tray
        self.setup_system_tray()

        # Create main window only if GUI is requested initially
        self.main_window = None
        if show_gui:
            self._create_main_window()

        # Connect signals (only if main window exists)
        if self.main_window:
            self.connect_signals()

        # Start background worker
        self.background_worker.start()

        # Load existing jobs from storage
        self.load_existing_jobs()

        # Show main window if requested (but main window might not exist yet)
        if show_gui and self.main_window:
            QTimer.singleShot(1000, self.show_main_window)  # Delay to ensure proper initialization

    def _create_main_window(self):
        """Create main window (lazy loading)."""
        if self.main_window is None:
            self.main_window = MainWindow(self.config, self.job_queue)
            self.connect_signals()

    def setup_logging(self):
        """Setup application logging."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=getattr(logging, self.config.config_data["logging"]["level"]),
            format=log_format,
            handlers=[
                logging.FileHandler(self.config.config_data["logging"]["file"]),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def show_config_errors(self, errors: list):
        """Show configuration errors to user."""
        error_text = "Errores de configuración encontrados:\n\n" + "\n".join(
            f"• {error}" for error in errors
        )

        if not QApplication.instance():
            # No GUI application yet, use console
            print(error_text)
            sys.exit(1)
        else:
            QMessageBox.critical(None, "Errores de configuración", error_text)
            sys.exit(1)

    def setup_system_tray(self):
        """Setup system tray icon and menu."""
        self.tray_icon = QSystemTrayIcon(self.app)

        # Try to load icon, fallback to default if not available
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Use default system icon - fix for PyQt5 compatibility
            from PyQt5.QtWidgets import QStyle

            self.tray_icon.setIcon(self.app.style().standardIcon(QStyle.SP_ComputerIcon))

        # Set tooltip
        self.tray_icon.setToolTip("EPSON PP-100 Disc Burner")

        # Create tray menu
        tray_menu = QMenu()

        # Show/Hide main window action
        self.show_action = QAction("Mostrar ventana principal", self.app)
        self.show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(self.show_action)

        # Status action
        self.status_action = QAction("Estado del sistema", self.app)
        self.status_action.triggered.connect(self.show_system_status)
        tray_menu.addAction(self.status_action)

        tray_menu.addSeparator()

        # Force API check action
        self.check_api_action = QAction("Verificar nuevos ISOs", self.app)
        self.check_api_action.triggered.connect(self.force_api_check)
        tray_menu.addAction(self.check_api_action)

        tray_menu.addSeparator()

        # Quit action
        quit_action = QAction("Salir", self.app)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Handle tray icon activation (double-click)
        self.tray_icon.activated.connect(self.on_tray_activated)

    def connect_signals(self):
        """Connect application signals."""
        if self.main_window:
            # Connect job manager signals to update GUI
            self.job_queue.add_job_update_callback(self.main_window.on_job_updated)

            # Connect main window signals to job queue
            self.main_window.job_updated.connect(self.on_job_updated_from_gui)

        # Connect tray icon messages
        self.tray_icon.messageClicked.connect(self.on_tray_message_clicked)

    def on_job_updated_from_gui(self, job):
        """Handle job updates from GUI."""
        # Update storage
        self.storage.update_job_status(job.id, job.status.value, job.error_message, job.progress)

        # Show notification for important status changes
        if job.status.value in ["completed", "failed"]:
            self.show_job_notification(job)

    def show_job_notification(self, job):
        """Show system notification for job status change."""
        if not self.config.show_notifications:
            return

        title = "Trabajo de quemado"
        message = f"Trabajo {job.id[:8]}... "

        if job.status.value == "completed":
            message += "completado exitosamente"
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
        elif job.status.value == "failed":
            message += f"falló: {job.error_message or 'Error desconocido'}"
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Critical, 10000)

    def load_existing_jobs(self):
        """Load existing jobs from storage."""
        try:
            jobs = self.storage.get_all_jobs()
            for job_record in jobs:
                # Convert storage record to job object
                iso_info = {
                    "id": job_record.iso_id,
                    "filename": job_record.filename,
                    "fileSize": job_record.file_size,
                    "downloadUrl": job_record.download_url,
                    "checksum": job_record.checksum,
                    "study": {
                        "patient": {
                            "fullName": job_record.study_patient_name,
                            "identifier": job_record.study_patient_id,
                            "birthDate": (
                                job_record.study_patient_birth_date.isoformat()
                                if job_record.study_patient_birth_date
                                else None
                            ),
                        },
                        "dicomDateTime": (
                            job_record.study_dicom_date_time.isoformat()
                            if job_record.study_dicom_date_time
                            else None
                        ),
                        "dicomDescription": job_record.study_dicom_description,
                    },
                    "fileUrl": job_record.download_url,  # GraphQL API uses fileUrl
                }

                # Create BurnJob from storage record
                from job_queue import BurnJob, JobPriority

                # Convert string status to enum
                try:
                    status_enum = JobStatus(job_record.status or "pending")
                except (ValueError, AttributeError):
                    status_enum = JobStatus.PENDING

                # Convert priority
                try:
                    priority_enum = (
                        JobPriority(job_record.priority)
                        if job_record.priority
                        else JobPriority.NORMAL
                    )
                except (ValueError, AttributeError):
                    priority_enum = JobPriority.NORMAL

                # Create BurnJob object
                job = BurnJob(
                    id=job_record.id,
                    iso_info=iso_info,
                    priority=priority_enum,
                    status=status_enum,
                    created_at=job_record.created_at or datetime.now(),
                    updated_at=job_record.updated_at or datetime.now(),
                    iso_path=job_record.iso_path,
                    jdf_path=job_record.jdf_path,
                    progress=job_record.progress or 0.0,
                    error_message=job_record.error_message,
                    retry_count=job_record.retry_count or 0,
                    robot_job_id=job_record.robot_job_id,
                    estimated_completion=job_record.estimated_completion,
                )

                # Add to job queue
                self.job_queue.jobs[job.id] = job

                # Add to queue if still needs processing
                if job.status in [
                    JobStatus.PENDING,
                    JobStatus.DOWNLOADING,
                    JobStatus.DOWNLOADED,
                    JobStatus.GENERATING_JDF,
                    JobStatus.JDF_READY,
                    JobStatus.QUEUED_FOR_BURNING,
                ]:
                    self.job_queue._insert_job_by_priority(job.id)

            self.logger.info(f"Loaded {len(jobs)} existing jobs from storage")

        except Exception as e:
            self.logger.error(f"Error loading existing jobs: {e}")

    def show_main_window(self):
        """Show the main application window."""
        self._create_main_window()  # Ensure window exists
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def hide_main_window(self):
        """Hide the main application window."""
        if self.main_window:
            self.main_window.hide()

    def on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()

    def show_system_status(self):
        """Show system status dialog."""
        self._create_main_window()  # Ensure window exists
        try:
            status = self.background_worker.get_worker_status()

            status_text = "Estado del Sistema EPSON PP-100:\n\n"

            # Queue status
            queue = status.get("queue_status", {})
            status_text += "Trabajos en cola:\n"
            status_text += f"  Total: {queue.get('total_jobs', 0)}\n"
            status_text += f"  Pendientes: {queue.get('pending', 0)}\n"
            status_text += f"  Quemando: {queue.get('burning', 0)}\n"
            status_text += f"  Completados: {queue.get('completed', 0)}\n"
            status_text += f"  Fallidos: {queue.get('failed', 0)}\n\n"

            # Storage stats
            storage = status.get("storage_stats", {})
            status_text += "Almacenamiento:\n"
            status_text += f"  Trabajos totales: {storage.get('total_jobs', 0)}\n"
            status_text += f"  Tamaño BD: {storage.get('database_size_mb', 0):.1f} MB\n\n"

            # Next API check
            next_check = status.get("next_api_check_in")
            if next_check:
                minutes = next_check // 60
                seconds = next_check % 60
                status_text += f"Próxima verificación API: en {minutes}:{seconds:02d}\n"
            else:
                status_text += "Próxima verificación API: Desconocida\n"

            QMessageBox.information(self.main_window, "Estado del Sistema", status_text)

        except Exception as e:
            QMessageBox.warning(self.main_window, "Error", f"Error obteniendo estado: {e}")

    def force_api_check(self):
        """Force an immediate API check for new ISOs."""
        self._create_main_window()  # Ensure window exists
        try:
            success = self.background_worker.trigger_api_check_now()

            if success:
                QMessageBox.information(
                    self.main_window,
                    "Verificación API",
                    "Verificación completada. Revisa los trabajos para ver si se agregaron nuevos ISOs.",
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "Verificación API",
                    "No se pudieron obtener nuevos ISOs o no hay conexión disponible.",
                )

        except Exception as e:
            QMessageBox.warning(self.main_window, "Error", f"Error en verificación API: {e}")

    def on_tray_message_clicked(self):
        """Handle tray message click - show main window."""
        self.show_main_window()

    def quit_application(self):
        """Quit the application completely."""
        # Confirm quit
        reply = QMessageBox.question(
            None,  # Use None since main window might not exist yet
            "Confirmar salida",
            "¿Está seguro de que desea salir?\nEsto detendrá todos los trabajos en progreso.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # Stop background worker
            self.background_worker.stop()

            # Save current state
            self.save_application_state()

            # Close main window if open
            if self.main_window and self.main_window.isVisible():
                self.main_window.close()

            # Quit application
            self.app.quit()

        except Exception as e:
            self.logger.error(f"Error during application quit: {e}")
            # Force quit
            self.app.quit()

    def save_application_state(self):
        """Save current application state."""
        try:
            # Update all job statuses in storage
            for job in self.job_queue.get_all_jobs():
                self.storage.update_job_status(
                    job.id, job.status.value, job.error_message, job.progress
                )

            self.logger.info("Application state saved")

        except Exception as e:
            self.logger.error(f"Error saving application state: {e}")

    def run(self):
        """Run the application."""
        return self.app.exec_()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="EPSON PP-100 Disc Burner Application")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run in background mode (system tray only, no GUI on startup)",
    )
    parser.add_argument("--test-config", action="store_true", help="Test configuration and exit")

    args = parser.parse_args()

    if args.test_config:
        # Test configuration without starting GUI
        try:
            from config import Config

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

    # Default behavior: show GUI
    # Use --background flag to run in system tray only mode
    show_gui = not args.background

    try:
        burner_app = EpsonBurnerApp(show_gui=show_gui)
        if hasattr(burner_app, "logger"):  # Check if app was properly initialized
            return burner_app.run()
        else:
            return 1
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
