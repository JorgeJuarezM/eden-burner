"""
Job Table Widget for EPSON PP-100 Disc Burner Application
"""

from typing import List, Optional

from PyQt5.QtCore import Q_ARG, QMetaObject, Qt, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHeaderView, QProgressBar, QTableWidget, QTableWidgetItem

from app.job_queue import BurnJob, JobStatus


class JobTableWidgetUI(QTableWidget):
    """Table widget UI class - handles only PyQt design and widget creation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize UI only
        self.setup_table()

    def setup_table(self):
        """Setup table headers and properties."""
        headers = [
            "ID",
            "Paciente",
            "Tipo",
            "Estado",
            "Creado",
        ]

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        # Resize columns
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Patient
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Progress

        # Set minimum column widths
        self.setColumnWidth(0, 50)  # ID
        self.setColumnWidth(1, 50)  # Patient
        self.setColumnWidth(2, 50)  # Type
        self.setColumnWidth(3, 200)  # Progress
        self.setColumnWidth(4, 50)  # Created


class JobTableWidgetLogic(JobTableWidgetUI):
    """Table widget logic class - inherits UI and adds business logic."""

    def __init__(self, parent=None):
        # Initialize the UI base class first
        super().__init__(parent)

    def update_jobs(self, jobs: List[BurnJob]):
        """Update table with job data.

        Args:
            jobs: List of jobs to display
        """
        # Schedule GUI update for main thread
        QMetaObject.invokeMethod(self, "_update_jobs_gui", Qt.QueuedConnection, Q_ARG(list, jobs))

    @pyqtSlot(list)
    def _update_jobs_gui(self, jobs: List[BurnJob]):
        """Update table GUI from main thread."""
        self.setRowCount(len(jobs))

        for row, job in enumerate(jobs):
            # Job ID (truncated)
            job_id_value = str(job.id).split("-")[-1]
            job_id_item = QTableWidgetItem(job_id_value)
            job_id_item.setToolTip(job.id)
            job_id_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 0, job_id_item)

            # Patient information
            study_info = job.iso_info.get("study", {})
            patient_info = study_info.get("patient", {})
            patient_name = patient_info.get("fullName", "Desconocido")
            patient_item = QTableWidgetItem(patient_name)
            patient_item.setToolTip(patient_name)
            patient_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 1, patient_item)

            # Disc type
            disc_type = job.disc_type or ""
            disc_type_item = QTableWidgetItem(disc_type)

            # Color code disc type
            if disc_type == "CD":
                disc_type_item.setForeground(QColor(173, 216, 230))  # Light blue for CD
            elif disc_type == "DVD":
                disc_type_item.setForeground(QColor(144, 238, 144))  # Light green for DVD
            elif disc_type == "Invalid":
                disc_type_item.setForeground(QColor(255, 182, 193))  # Light pink for invalid
            else:
                disc_type_item.setForeground(QColor(211, 211, 211))  # Light gray for unknown

            disc_type_item.setToolTip(
                f"Tipo de disco: {disc_type}" if disc_type else "Tipo de disco aún no detectado"
            )
            # disc_type_item.setForeground(QColor(0, 0, 0))  # Black text for better contrast
            self.setItem(row, 2, disc_type_item)

            # Progress bar with custom text (compact design)
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(job.progress))
            progress_bar.setTextDirection(QProgressBar.Direction.TopToBottom)
            progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # progress_bar.setFixedHeight(20)  # Compact height
            progress_bar.setValue(0)  # Reset progress bar

            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #004875; }")

            # Set custom text based on status with enhanced dark theme colors
            if job.status == JobStatus.COMPLETED:
                progress_bar.setFormat("✓ Completado")
            elif job.status == JobStatus.FAILED:
                progress_bar.setFormat("✗ Fallido")
            elif job.status == JobStatus.DOWNLOADING:
                progress_bar.setValue(int(job.progress))
                progress_bar.setFormat(f"📥 Descargando {int(job.progress)}%")
            elif job.status == JobStatus.BURNING:
                progress_bar.setFormat(f"🔥 Quemando {int(job.progress)}%")
            elif job.status == JobStatus.CANCELLED:
                progress_bar.setFormat("✗ Cancelado")
            elif job.status == JobStatus.PENDING:
                progress_bar.setFormat("⏳ Pendiente")
            else:
                progress_bar.setFormat("⏳ Esperando...")

            self.setCellWidget(row, 3, progress_bar)

            # Created time
            created_item = QTableWidgetItem(job.created_at.strftime("%Y-%m-%d %H:%M"))
            created_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 4, created_item)

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


# JobTableWidgetLogic is the complete table widget class that combines UI and Logic
JobTableWidget = JobTableWidgetLogic
