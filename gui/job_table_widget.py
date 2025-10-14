"""
Job Table Widget for EPSON PP-100 Disc Burner Application
"""

from typing import List, Optional

from PyQt5.QtCore import Q_ARG, QMetaObject, Qt, pyqtSlot
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHeaderView, QProgressBar, QTableWidget, QTableWidgetItem

from src.job_queue import BurnJob, JobStatus


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
            "Estudio",
            "Estado",
            "Progreso",
            "Creado",
            "Actualizado",
        ]

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        # Set better colors for alternating rows and selection with white text
        self.setStyleSheet(
            """
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
        """
        )

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

            # ISO filename
            # iso_name = job.iso_info.get("filename", "Unknown")
            # iso_item = QTableWidgetItem(iso_name)
            # iso_item.setForeground(QColor(255, 255, 255))  # White text
            # self.setItem(row, 1, iso_item)

            # Patient information
            study_info = job.iso_info.get("study", {})
            patient_info = study_info.get("patient", {})
            patient_name = patient_info.get("fullName", "Desconocido")
            patient_item = QTableWidgetItem(patient_name)
            patient_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 1, patient_item)

            # Study information
            study_desc = study_info.get("dicomDescription", "Sin descripción")
            if len(study_desc) > 50:
                study_desc = study_desc[:47] + "..."
            study_item = QTableWidgetItem(study_desc)
            study_item.setToolTip(study_info.get("dicomDescription", ""))
            study_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 2, study_item)

            # Status with color coding
            status_item = QTableWidgetItem(job.status.value.title())
            status_item.setToolTip(f"Estado: {job.status.value}")

            # Color code by status with better contrast
            if job.status.value == JobStatus.COMPLETED.value:
                status_item.setBackground(QColor(76, 175, 80))  # Green 600
                status_item.setForeground(QColor(255, 255, 255))  # White text
            elif job.status.value == JobStatus.FAILED.value:
                status_item.setBackground(QColor(244, 67, 54))  # Red 600
                status_item.setForeground(QColor(255, 255, 255))  # White text
            elif job.status.value in [JobStatus.BURNING.value, JobStatus.VERIFYING.value]:
                status_item.setBackground(QColor(33, 150, 243))  # Blue 600
                status_item.setForeground(QColor(255, 255, 255))  # White text
            elif job.status.value == JobStatus.DOWNLOADING.value:
                status_item.setBackground(QColor(255, 193, 7))  # Amber 600
                status_item.setForeground(QColor(0, 0, 0))  # Black text for better contrast
            elif job.status.value == JobStatus.DOWNLOADED.value:
                status_item.setBackground(
                    QColor(139, 195, 74)
                )  # Light green (different from completed)
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
            progress_bar.setTextDirection(QProgressBar.Direction.TopToBottom)
            progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Custom styling for progress bar
            if job.status == JobStatus.COMPLETED:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #57c24f; }")
            elif job.status == JobStatus.FAILED:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFB6C1; }")
            else:
                progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #57c24f; }")

            self.setCellWidget(row, 4, progress_bar)

            # Created time
            created_item = QTableWidgetItem(job.created_at.strftime("%Y-%m-%d %H:%M"))
            created_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 5, created_item)

            # Updated time
            updated_item = QTableWidgetItem(job.updated_at.strftime("%Y-%m-%d %H:%M"))
            updated_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 6, updated_item)

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
