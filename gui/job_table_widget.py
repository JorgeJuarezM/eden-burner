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
            "Estado",
            "Creado",
        ]

        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

        # Enhanced dark theme styles for table
        self.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #555555;
                selection-background-color: #1976D2;
                selection-color: #FFFFFF;
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3c3c3c;
            }
            QTableWidget::item:selected {
                background-color: #1976D2;
                color: #ffffff;
            }
            QTableWidget::item:alternate {
                background-color: #333333;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #4a4a4a;
            }
            QScrollBar:vertical {
                background-color: #3c3c3c;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background-color: #3c3c3c;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #666666;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """
        )

        # Resize columns
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Patient
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Progress

        # Set minimum column widths
        self.setColumnWidth(0, 50)  # ID
        self.setColumnWidth(1, 50)  # Patient
        self.setColumnWidth(2, 200)  # Progress
        self.setColumnWidth(3, 50)  # Created


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

            # Progress bar with custom text
            progress_bar = QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setValue(int(job.progress))
            progress_bar.setTextDirection(QProgressBar.Direction.TopToBottom)
            progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Set custom text based on status with enhanced dark theme colors
            if job.status == JobStatus.COMPLETED:
                progress_bar.setValue(100)  # Ensure full progress for completed
                progress_bar.setFormat("✓ Completado")
                progress_bar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                        background-color: #1B5E20;
                        font-size: 12px;
                    }
                    QProgressBar::chunk {
                        background-color: #4CAF50;
                        border-radius: 6px;
                    }
                """
                )
            elif job.status == JobStatus.FAILED:
                progress_bar.setValue(100)  # Ensure full progress for failed
                progress_bar.setFormat("✗ Fallido")
                progress_bar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 2px solid #F44336;
                        border-radius: 8px;
                        background-color: #B71C1C;
                        font-size: 12px;
                    }
                    QProgressBar::chunk {
                        background-color: #F44336;
                        border-radius: 6px;
                    }
                """
                )
            elif job.status == JobStatus.DOWNLOADING:
                progress_bar.setFormat(f"📥 Descargando {int(job.progress)}%")
                progress_bar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 2px solid #FF9800;
                        border-radius: 8px;
                        background-color: #E65100;
                        font-size: 12px;
                    }
                    QProgressBar::chunk {
                        background-color: #FF9800;
                        border-radius: 6px;
                    }
                """
                )
            elif job.status == JobStatus.DOWNLOADED:
                progress_bar.setValue(100)  # Ensure full progress for downloaded
                progress_bar.setFormat("📁 Descargado")
                progress_bar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 2px solid #8BC34A;
                        border-radius: 8px;
                        background-color: #33691E;
                        font-size: 12px;
                    }
                    QProgressBar::chunk {
                        background-color: #8BC34A;
                        border-radius: 6px;
                    }
                """
                )
            elif job.status == JobStatus.BURNING:
                progress_bar.setFormat(f"🔥 Quemando {int(job.progress)}%")
                progress_bar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 2px solid #2196F3;
                        border-radius: 8px;
                        background-color: #0D47A1;
                        font-size: 12px;
                    }
                    QProgressBar::chunk {
                        background-color: #2196F3;
                        border-radius: 6px;
                    }
                """
                )
            elif job.status == JobStatus.VERIFYING:
                progress_bar.setFormat(f"🔍 Verificando {int(job.progress)}%")
                progress_bar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 2px solid #9C27B0;
                        border-radius: 8px;
                        background-color: #4A148C;
                        font-size: 12px;
                    }
                    QProgressBar::chunk {
                        background-color: #9C27B0;
                        border-radius: 6px;
                    }
                """
                )
            else:  # PENDING or other status
                progress_bar.setValue(0)  # No progress for pending
                progress_bar.setFormat("⏳ Pendiente")
                progress_bar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        color: #FFFFFF;
                        font-weight: bold;
                        border: 2px solid #9E9E9E;
                        border-radius: 8px;
                        background-color: #424242;
                        font-size: 12px;
                    }
                    QProgressBar::chunk {
                        background-color: #9E9E9E;
                        border-radius: 6px;
                    }
                """
                )

            self.setCellWidget(row, 2, progress_bar)

            # Created time
            created_item = QTableWidgetItem(job.created_at.strftime("%Y-%m-%d %H:%M"))
            created_item.setForeground(QColor(255, 255, 255))  # White text
            self.setItem(row, 3, created_item)

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
