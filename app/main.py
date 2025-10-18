#!/usr/bin/env python3
"""
EPSON PP-100 Disc Burner Application

A professional PyQt5 application for managing ISO burning jobs with EPSON PP-100 robot.

Architecture:
    - 3-layer architecture with clean separation of concerns
    - Data layer (db/): SQLAlchemy ORM and repository pattern
    - Business logic layer (app/): Core application functionality
    - Presentation layer (gui/): PyQt5 user interface

Features:
    - GraphQL API integration for automatic ISO discovery
    - Multi-task job queue management with priority support
    - JDF file generation for robot communication
    - Background execution support with system tray integration
    - Intuitive GUI for job monitoring and configuration
    - DICOM study information processing and display
    - Template-based file generation (JDF, labels, data files)
    - SQLite database with automatic backups
    - Cross-platform compatibility (Windows, macOS, Linux)

Command Line Options:
    --background: Run in background mode (system tray only)
    --test-config: Validate configuration and exit
    --clear-database: Clear database and exit
"""

import logging
import os
import sys
from datetime import datetime

import qdarktheme
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
)

import db
from app.background_worker import BackgroundWorker
from app.job_queue import BurnJob, JobQueue, JobStatus
from app.local_storage import LocalStorage
from config.config import Config
from gui.main_window import MainWindow

app_config = Config.get_current_config()


class EpsonBurnerApp:
    """
    Main application class for EPSON PP-100 disc burner management.

    This class serves as the central coordinator for the entire application,
    managing the lifecycle of all components including GUI, background workers,
    job queue, and database operations.

    Architecture:
        - Coordinates between GUI (PyQt5) and business logic
        - Manages background worker threads for API polling and job processing
        - Handles system tray integration and notifications
        - Provides centralized configuration management
        - Manages database initialization and job loading

    Components:
        - storage: Local database management (backup, cleanup)
        - job_queue: Multi-threaded job processing queue
        - background_worker: API polling and job scheduling
        - main_window: GUI interface (lazy-loaded)
        - tray_icon: System tray integration

    Threading:
        - Main thread: GUI and user interactions
        - Background thread: API polling and job processing
        - Worker threads: Individual job processing tasks
    """

    def __init__(self):
        """
        Initialize the EPSON PP-100 Disc Burner application.

        This constructor sets up the complete application environment including:
        - Logging configuration using application settings
        - Configuration validation and error handling
        - Required folder structure creation
        - Core component initialization (storage, job queue, background worker)
        - PyQt5 application setup with system tray support

        The initialization follows a fail-fast approach - if configuration
        is invalid, the application exits immediately with detailed error messages.
        """
        # Setup logging (now that config is available)
        self.setup_logging()

        # Validate configuration
        config_errors = app_config.validate_config()
        if config_errors:
            self.show_config_errors(config_errors)
            return

        # Ensure folders exist
        app_config.ensure_folders_exist()

        # Initialize core components
        self.storage = LocalStorage()
        self.job_queue = JobQueue()
        self.background_worker = BackgroundWorker(self.job_queue)

        # Setup application
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        pallete = qdarktheme.load_palette(theme="dark")
        self.app.setPalette(pallete)

        stylesheet = qdarktheme.load_stylesheet(theme="dark")
        self.app.setStyleSheet(stylesheet)

    def initialize_application(self, show_gui=False):
        """
        Initialize and start the complete application system.

        This method performs the full application bootstrap including database setup,
        system tray integration, GUI initialization, and background processing startup.

        Args:
            show_gui (bool): Whether to show the main window immediately.
                           If False, application runs in system tray mode only.

        Raises:
            Exception: If database migration fails or critical initialization errors occur.

        The initialization sequence ensures:
        1. Database schema is up to date
        2. System tray is properly configured
        3. GUI is created (if requested)
        4. Signal connections are established
        5. Background worker starts processing
        6. Existing jobs are loaded from storage
        7. GUI is shown after a brief delay for proper initialization
        """
        # Migrate database
        success = self.storage.migrate_database()
        if not success:
            self.logger.error("Error migrating database")
            raise Exception("Error migrating database")

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
        """
        Create main window using lazy loading pattern.

        This method implements lazy initialization for the main GUI window,
        creating it only when first needed. This improves startup performance
        and reduces memory usage when running in background mode.

        The method ensures:
        - Window is created only once (singleton pattern)
        - Signal connections are established after creation
        - Proper error handling for window creation failures
        """
        if self.main_window is None:
            self.main_window = MainWindow(self.job_queue)
            self.connect_signals()

    def setup_logging(self):
        """
        Configure application-wide logging system.

        Sets up structured logging using configuration from app_config with:
        - File logging for persistent records
        - Console logging for development/debugging
        - Configurable log levels (DEBUG, INFO, WARNING, ERROR)
        - Timestamped log format for better traceability

        The logging configuration is read from:
        - config_data["logging"]["level"]: Log level (DEBUG, INFO, etc.)
        - config_data["logging"]["file"]: Log file path for file handler

        This method must be called early in application initialization
        to ensure all subsequent logging calls are properly configured.
        """
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=getattr(logging, app_config.config_data["logging"]["level"]),
            format=log_format,
            handlers=[
                logging.FileHandler(app_config.config_data["logging"]["file"]),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def show_config_errors(self, errors: list):
        """
        Display configuration validation errors to the user.

        This method handles configuration errors discovered during application
        initialization. It provides both console and GUI feedback depending
        on whether the QApplication has been initialized.

        Args:
            errors (list): List of configuration error messages to display.

        The method formats errors as a bulleted list and shows them either:
        - In console (if QApplication not yet initialized)
        - In a critical message box (if GUI is available)

        After displaying errors, the application exits with code 1 to prevent
        running with invalid configuration.
        """
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
        """
        Initialize and configure the system tray icon and menu.

        This method sets up the complete system tray integration including:
        - Icon loading with fallback to system default
        - Tooltip configuration
        - Context menu with all available actions
        - Signal connections for tray interactions

        The system tray provides background operation capabilities when
        the main window is closed, allowing users to:
        - Show/hide the main window
        - Check system status
        - Force API checks for new ISOs
        - Quit the application

        Icon Strategy:
        1. Try to load custom application icon from assets
        2. Fallback to system computer icon if custom not available
        3. Ensure PyQt5 compatibility with icon loading

        Menu Actions:
        - Show/Hide: Toggle main window visibility
        - System Status: Display current system statistics
        - Force API Check: Manually trigger ISO discovery
        - Quit: Graceful application shutdown
        """
        self.tray_icon = QSystemTrayIcon(self.app)

        # Try to load icon, fallback to default if not available
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Use default system icon - fix for PyQt5 compatibility
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
        db.BurnJob.update_job_state(job, commit=True)

        # Show notification for important status changes
        if job.status.value in ["completed", "failed"]:
            self.show_job_notification(job)

    def show_job_notification(self, job: BurnJob):
        """Show system notification for job status change."""
        if not app_config.show_notifications or job.notification_sent:
            return

        title = "Trabajo de quemado"
        message = f"Trabajo {job.id[:8]}... "

        if job.status.value == "completed":
            message += "completado exitosamente"
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 5000)
            job.notification_sent = True
        elif job.status.value == "failed":
            message += f"falló: {job.error_message or 'Error desconocido'}"
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Critical, 10000)
            job.notification_sent = True

    def load_existing_jobs(self):
        """Load existing jobs from storage."""
        try:
            jobs = db.BurnJob.get_all_jobs()
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

                # Convert string status to enum
                try:
                    status_enum = JobStatus(job_record.status or "pending")
                except (ValueError, AttributeError):
                    status_enum = JobStatus.PENDING

                # Create BurnJob object
                job = BurnJob(
                    id=job_record.id,
                    iso_info=iso_info,
                    status=status_enum,
                    created_at=job_record.created_at or datetime.now(),
                    updated_at=job_record.updated_at or datetime.now(),
                    iso_path=job_record.iso_path,
                    jdf_path=job_record.jdf_path,
                    progress=job_record.progress or 0.0,
                    error_message=job_record.error_message,
                    retry_count=job_record.retry_count or 0,
                    disc_type=job_record.disc_type,
                    robot_job_id=job_record.robot_job_id,
                    estimated_completion=job_record.estimated_completion,
                )

                # Override in progress statuses
                if job.status == JobStatus.BURNING:
                    job.status = JobStatus.QUEUED_FOR_BURNING
                elif job.status == JobStatus.DOWNLOADING:
                    job.status = JobStatus.PENDING
                elif job.status == JobStatus.GENERATING_JDF:
                    job.status = JobStatus.DOWNLOADED

                # Add to job queue
                self.job_queue.jobs[job.id] = job

                # Add to queue if still needs processing
                if job.status not in [
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                ]:
                    self.job_queue.job_queue.append(job.id)

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
                db.BurnJob.update_job_state(job, commit=True)

            self.logger.info("Application state saved")

        except Exception as e:
            self.logger.error(f"Error saving application state: {e}")

    def run(self):
        """Run the application."""
        return self.app.exec_()
