"""
PyQt GUI for EPSON PP-100 Disc Burner Application
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                           QPushButton, QLabel, QProgressBar, QStatusBar, QMenuBar,
                           QAction, QMessageBox, QSplitter, QGroupBox, QTextEdit,
                           QComboBox, QLineEdit, QFormLayout, QSpinBox, QCheckBox,
                           QSystemTrayIcon, QMenu, QStyle, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette

from config import Config
from job_queue import JobQueue, BurnJob, JobStatus, JobPriority
from local_storage import LocalStorage


class JobTableWidget(QTableWidget):
    """Custom table widget for displaying jobs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()

    def setup_table(self):
        """Setup table headers and properties."""
        headers = ['ID', 'Paciente', 'Estudio', 'Estado', 'Progreso', 'Prioridad', 'Creado', 'Actualizado']

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set better colors for alternating rows and selection with white text
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #555555;
                selection-background-color: #1976D2;
                selection-color: #FFFFFF;
                background-color: #424242;
                color: #FFFFFF;
            }
            QTableWidget::item {
                color: #FFFFFF;
            }
            QTableWidget::item:alternate {
                background-color: #484848;
            }
            QTableWidget::item:selected {
                background-color: #1976D2;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: #333333;
                color: #FFFFFF;
                border: 1px solid #555555;
            }
        """)

        # Resize columns
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID column
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status column

        # Set minimum column widths
        self.setColumnWidth(0, 100)  # ID
        self.setColumnWidth(1, 200)  # Patient
        self.setColumnWidth(2, 200)  # Study
        self.setColumnWidth(3, 100)  # Status
        self.setColumnWidth(4, 150)  # Progress
        self.setColumnWidth(5, 80)   # Priority

    def update_jobs(self, jobs: List[BurnJob]):
        """Update table with job data.

        Args:
            jobs: List of jobs to display
        """
        # Schedule GUI update for main thread
        QMetaObject.invokeMethod(
            self, "_update_jobs_gui",
            Qt.QueuedConnection,
            Q_ARG(list, jobs)
        )

    @pyqtSlot(list)
    def _update_jobs_gui(self, jobs: List[BurnJob]):
        """Update table GUI from main thread."""
        self.setRowCount(len(jobs))

        for row, job in enumerate(jobs):
            # Job ID (truncated)
            job_id_item = QTableWidgetItem(job.id[:8] + '...')
            job_id_item.setToolTip(job.id)
            job_id_item.setFont(QFont('Courier New', 9))
            job_id_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 0, job_id_item)

            # ISO filename
            iso_name = job.iso_info.get('filename', 'Unknown')
            iso_item = QTableWidgetItem(iso_name)
            iso_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 1, iso_item)

            # Patient information
            study_info = job.iso_info.get('study', {})
            patient_info = study_info.get('patient', {})
            patient_name = patient_info.get('fullName', 'Desconocido')
            patient_item = QTableWidgetItem(patient_name)
            patient_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 1, patient_item)

            # Study information  
            study_desc = study_info.get('dicomDescription', 'Sin descripción')
            if len(study_desc) > 50:
                study_desc = study_desc[:47] + '...'
            study_item = QTableWidgetItem(study_desc)
            study_item.setToolTip(study_info.get('dicomDescription', ''))
            study_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 2, study_item)

            # Status with color coding
            status_item = QTableWidgetItem(job.status.value.title())
            status_item.setToolTip(f"Estado: {job.status.value}")

            # Color code by status with better contrast
            if job.status == JobStatus.COMPLETED:
                status_item.setBackground(QColor(76, 175, 80))  # Green 600
                status_item.setForeground(QColor(255, 255, 255))  # White text
            elif job.status == JobStatus.FAILED:
                status_item.setBackground(QColor(244, 67, 54))  # Red 600
                status_item.setForeground(QColor(255, 255, 255))  # White text
            elif job.status in [JobStatus.BURNING, JobStatus.VERIFYING]:
                status_item.setBackground(QColor(33, 150, 243))  # Blue 600
                status_item.setForeground(QColor(255, 255, 255))  # White text
            elif job.status == JobStatus.DOWNLOADING:
                status_item.setBackground(QColor(255, 193, 7))  # Amber 600
                status_item.setForeground(QColor(0, 0, 0))  # Black text for better contrast
            elif job.status == JobStatus.DOWNLOADED:
                status_item.setBackground(QColor(139, 195, 74))  # Light green (different from completed)
                status_item.setForeground(QColor(0, 0, 0))  # Black text for better contrast
            else:
                # Default/PENDING status - light background, black text
                status_item.setBackground(QColor(224, 224, 224))  # Light gray background
                status_item.setForeground(QColor(0, 0, 0))  # Black text

            self.setItem(row, 3, status_item)

            # Progress bar
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(job.progress))

            # Custom styling for progress bar
            if job.status == JobStatus.COMPLETED:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #90EE90; }")
            elif job.status == JobStatus.FAILED:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFB6C1; }")
            else:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ADD8E6; }")

            self.setCellWidget(row, 4, progress_bar)

            # Priority
            priority_text = {
                JobPriority.LOW: 'Baja',
                JobPriority.NORMAL: 'Normal',
                JobPriority.HIGH: 'Alta',
                JobPriority.URGENT: 'Urgente'
            }
            priority_item = QTableWidgetItem(priority_text.get(job.priority, 'Normal'))
            priority_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 5, priority_item)

            # Created time
            created_item = QTableWidgetItem(job.created_at.strftime('%Y-%m-%d %H:%M'))
            created_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 6, created_item)

            # Updated time
            updated_item = QTableWidgetItem(job.updated_at.strftime('%Y-%m-%d %H:%M'))
            updated_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 7, updated_item)

    def get_selected_job_id(self) -> Optional[str]:
        """Get the ID of the currently selected job.

        Returns:
            Job ID or None if no selection
        """
        current_row = self.currentRow()
        if current_row >= 0:
            job_id_item = self.item(current_row, 0)
            if job_id_item:
                return job_id_item.toolTip()  # Full job ID is in tooltip
        return None


class JobDetailsWidget(QWidget):
    """Widget for displaying detailed job information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)

        # Job info group
        info_group = QGroupBox("Información del Trabajo")
        info_layout = QFormLayout()

        self.job_id_label = QLabel('--')
        self.job_id_label.setFont(QFont('Courier New', 10, QFont.Bold))
        info_layout.addRow("ID:", self.job_id_label)

        self.status_label = QLabel('--')
        info_layout.addRow("Estado:", self.status_label)

        self.filename_label = QLabel('--')
        info_layout.addRow("Archivo ISO:", self.filename_label)

        # Patient information
        self.patient_label = QLabel('--')
        info_layout.addRow("Paciente:", self.patient_label)

        # Study information
        self.study_label = QLabel('--')
        info_layout.addRow("Estudio:", self.study_label)

        self.progress_label = QLabel('--')
        info_layout.addRow("Progreso:", self.progress_label)

        self.created_label = QLabel('--')
        info_layout.addRow("Creado:", self.created_label)

        self.updated_label = QLabel('--')
        info_layout.addRow("Actualizado:", self.updated_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # History group
        history_group = QGroupBox("Historial")
        history_layout = QVBoxLayout()

        self.history_text = QTextEdit()
        self.history_text.setMaximumHeight(150)
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)

        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.retry_button = QPushButton("Reintentar")
        self.retry_button.setEnabled(False)
        self.retry_button.clicked.connect(self.on_retry_clicked)
        button_layout.addWidget(self.retry_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

    def update_job_details(self, job: Optional[BurnJob]):
        """Update the widget with job details.

        Args:
            job: Job to display or None to clear
        """
        if job is None:
            self.clear_details()
            return

        # Update labels
        self.job_id_label.setText(job.id[:16] + '...' if len(job.id) > 16 else job.id)
        self.status_label.setText(job.status.value.title())
        self.filename_label.setText(job.iso_info.get('filename', 'Unknown'))

        # Patient information
        study_info = job.iso_info.get('study', {})
        patient_info = study_info.get('patient', {})
        patient_name = patient_info.get('fullName', 'Desconocido')
        patient_id = patient_info.get('identifier', 'N/A')
        self.patient_label.setText(f"{patient_name} (ID: {patient_id})")

        # Study information
        study_desc = study_info.get('dicomDescription', 'Sin descripción')
        study_datetime = study_info.get('dicomDateTime', 'N/A')
        self.study_label.setText(f"{study_desc[:50]}..." if len(study_desc) > 50 else study_desc)

        self.progress_label.setText(f"{job.progress:.1f}%")
        self.created_label.setText(job.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        self.updated_label.setText(job.updated_at.strftime('%Y-%m-%d %H:%M:%S'))

        # Update progress bar
        self.progress_bar.setValue(int(job.progress))

        # Color code progress bar
        if job.status == JobStatus.COMPLETED:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #90EE90; }")
        elif job.status == JobStatus.FAILED:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFB6C1; }")
        else:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ADD8E6; }")

        # Update button states
        self.retry_button.setEnabled(job.status == JobStatus.FAILED)
        self.cancel_button.setEnabled(job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED])

        # Update history (placeholder for now)
        self.history_text.clear()
        self.history_text.append(f"Trabajo creado: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if job.error_message:
            self.history_text.append(f"Error: {job.error_message}")

    def clear_details(self):
        """Clear all job details."""
        self.job_id_label.setText('--')
        self.status_label.setText('--')
        self.filename_label.setText('--')
        self.patient_label.setText('--')
        self.study_label.setText('--')
        self.progress_label.setText('--')
        self.created_label.setText('--')
        self.updated_label.setText('--')
        self.progress_bar.setValue(0)
        self.retry_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.history_text.clear()

    def on_retry_clicked(self):
        """Handle retry button click."""
        # Emit signal for parent to handle
        pass

    def on_cancel_clicked(self):
        """Handle cancel button click."""
        # Emit signal for parent to handle
        pass


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals
    job_updated = pyqtSignal(object)  # BurnJob
    job_completed = pyqtSignal(str)   # job_id
    job_failed = pyqtSignal(str)      # job_id

    def __init__(self, config: Config, job_queue: JobQueue):
        super().__init__()
        self.config = config
        self.job_queue = job_queue
        self.selected_job_id = None

        self.setup_ui()
        self.setup_connections()
        self.setup_timers()

        # Load initial data
        self.refresh_data()

    def setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle(self.config.window_title)
        self.setMinimumSize(1000, 700)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - Job list
        left_panel = self.create_job_list_panel()
        splitter.addWidget(left_panel)

        # Right panel - Job details
        right_panel = self.create_job_details_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()

        # Menu bar
        self.setup_menu_bar()

    def create_job_list_panel(self):
        """Create the job list panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Panel title
        title_label = QLabel("Trabajos de Quemado")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        layout.addWidget(title_label)

        # Filter controls
        filter_layout = QHBoxLayout()

        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos", "all")
        self.status_filter.addItem("Pendientes", "pending")
        self.status_filter.addItem("Descargando", "downloading")
        self.status_filter.addItem("Quemando", "burning")
        self.status_filter.addItem("Completados", "completed")
        self.status_filter.addItem("Fallidos", "failed")
        self.status_filter.currentTextChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(QLabel("Filtrar:"))
        filter_layout.addWidget(self.status_filter)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Job table
        self.job_table = JobTableWidget()
        self.job_table.setMaximumHeight(400)
        self.job_table.itemSelectionChanged.connect(self.on_job_selection_changed)
        layout.addWidget(self.job_table)

        # Queue status
        self.queue_status_label = QLabel("Estado de la cola: --")
        layout.addWidget(self.queue_status_label)

        # Control buttons
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)

        self.clear_completed_button = QPushButton("Limpiar Completados")
        self.clear_completed_button.clicked.connect(self.clear_completed_jobs)
        button_layout.addWidget(self.clear_completed_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        return panel

    def create_job_details_panel(self):
        """Create the job details panel."""
        self.job_details = JobDetailsWidget()
        return self.job_details

    def setup_menu_bar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('Archivo')

        settings_action = QAction('Configuración', self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction('Salir', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu('Herramientas')

        test_api_action = QAction('Probar Conexión API', self)
        test_api_action.triggered.connect(self.test_api_connection)
        tools_menu.addAction(test_api_action)

        # Help menu
        help_menu = menubar.addMenu('Ayuda')

        about_action = QAction('Acerca de', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_connections(self):
        """Setup signal connections."""
        # Connect job queue signals
        self.job_queue.add_job_update_callback(self.on_job_updated)

    def setup_timers(self):
        """Setup update timers."""
        # Timer for refreshing data
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(self.config.gui_refresh_interval)

        # Timer for updating status bar
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(5000)  # Every 5 seconds

    def on_job_updated(self, job: BurnJob):
        """Handle job update signal."""
        self.job_updated.emit(job)
        self.refresh_job_display()

    def on_job_selection_changed(self):
        """Handle job selection change in table."""
        job_id = self.job_table.get_selected_job_id()
        if job_id:
            job = self.job_queue.get_job(job_id)
            if job:
                self.job_details.update_job_details(job)
                self.selected_job_id = job_id
        else:
            self.job_details.clear_details()
            self.selected_job_id = None

    def on_filter_changed(self):
        """Handle filter change."""
        self.refresh_job_display()

    def refresh_data(self):
        """Refresh all displayed data."""
        self.refresh_job_display()
        self.update_status_bar()

    def refresh_job_display(self):
        """Refresh the job table display."""
        filter_status = self.status_filter.currentData()

        if filter_status == "all":
            jobs = self.job_queue.get_all_jobs()
        else:
            # Map filter to status
            status_map = {
                "pending": JobStatus.PENDING,
                "downloading": JobStatus.DOWNLOADING,
                "burning": JobStatus.BURNING,
                "completed": JobStatus.COMPLETED,
                "failed": JobStatus.FAILED
            }
            status = status_map.get(filter_status)
            if status:
                jobs = self.job_queue.get_jobs_by_status(status)
            else:
                jobs = []

        # Sort jobs by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        self.job_table.update_jobs(jobs)

    def update_status_bar(self):
        """Update the status bar with current information."""
        try:
            queue_status = self.job_queue.get_queue_status()

            status_text = (
                f"Total: {queue_status['total_jobs']} | "
                f"Pendientes: {queue_status['pending']} | "
                f"Quemando: {queue_status['burning']} | "
                f"Completados: {queue_status['completed']} | "
                f"Fallidos: {queue_status['failed']}"
            )

            self.status_bar.showMessage(status_text)

        except Exception as e:
            self.status_bar.showMessage(f"Error updating status: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        # Hide window instead of closing
        event.ignore()
        self.hide()

        # Show message to user
        QMessageBox.information(
            self,
            "Aplicación minimizada",
            "La aplicación continúa ejecutándose en segundo plano.\n"
            "Use el ícono de la bandeja del sistema para restaurarla."
        )

    def show_settings(self):
        """Show settings dialog."""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Configuración", "Diálogo de configuración no implementado aún.")

    def test_api_connection(self):
        """Test API connection."""
        try:
            # This would use the job queue's download manager to test connection
            QMessageBox.information(self, "Prueba de conexión", "Prueba de conexión no implementada aún.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error en prueba de conexión: {e}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "Acerca de EPSON PP-100 Disc Burner",
            "Aplicación para gestión de quemado de discos con robot EPSON PP-100\n\n"
            "Características:\n"
            "- Consulta de ISOs vía GraphQL API\n"
            "- Gestión de cola de trabajos\n"
            "- Generación automática de archivos JDF\n"
            "- Interfaz intuitiva para monitoreo\n"
            "- Ejecución en segundo plano\n\n"
            "Versión 1.0"
        )

    def clear_completed_jobs(self):
        """Clear completed jobs from display and storage."""
        try:
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                'Confirmar limpieza',
                '¿Está seguro de que desea limpiar los trabajos completados?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # This would clean up completed jobs from storage
                QMessageBox.information(self, "Limpieza", "Limpieza no implementada aún.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error limpiando trabajos: {e}")
