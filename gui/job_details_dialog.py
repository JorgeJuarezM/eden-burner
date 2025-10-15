"""
Job Details Dialog for EPSON PP-100 Disc Burner Application
"""

from typing import Optional

from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from src.job_queue import BurnJob, JobStatus


class JobDetailsDialogUI(QDialog):
    """Dialog UI class - handles only PyQt design and widget creation."""

    def __init__(self, job: BurnJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.job_id = job.id

        # Initialize UI only
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle(f"Detalles del Trabajo - {self.job.id[:16]}...")
        self.setMinimumSize(600, 500)
        self.setStyleSheet(
            """
            QDialog {
                background-color: #000000;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 4px 6px;
                font-size: 11px;
            }
            QLineEdit:read-only {
                background-color: #111111;
                color: #cccccc;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 3px;
                margin-top: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
                color: #ffffff;
                background-color: #000000;
            }
            QProgressBar {
                border: 1px solid #333333;
                border-radius: 2px;
                background-color: #1a1a1a;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 1px;
            }
            QPushButton {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 2px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #222222;
            }
            QPushButton:disabled {
                background-color: #111111;
                color: #666666;
                border-color: #222222;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 2px;
                padding: 4px 6px;
                font-size: 11px;
            }
        """
        )

        layout = QVBoxLayout(self)

        # Job info group
        info_group = QGroupBox("Información del Trabajo")
        info_layout = QFormLayout()

        # Job ID - show complete ID with normal font size
        self.job_id_txt = QLineEdit("--")
        self.job_id_txt.setReadOnly(True)
        self.job_id_txt.setMinimumWidth(400)
        self.job_id_txt.setMaximumWidth(400)
        self.job_id_txt.setStyleSheet("QTextEdit { background-color: #313131; color: #ffffff; }")
        info_layout.addRow("ID:", self.job_id_txt)

        self.status_label = QLabel("--")
        info_layout.addRow("Estado:", self.status_label)

        self.filename_label = QLabel("--")
        info_layout.addRow("Archivo ISO:", self.filename_label)

        self.disc_type_label = QLabel("--")
        info_layout.addRow("Tipo de Disco:", self.disc_type_label)

        # Patient information
        self.patient_label = QLabel("--")
        info_layout.addRow("Paciente:", self.patient_label)

        # Study information
        self.study_label = QLabel("--")
        info_layout.addRow("Estudio:", self.study_label)

        self.progress_label = QLabel("--")
        info_layout.addRow("Progreso:", self.progress_label)

        self.created_label = QLabel("--")
        info_layout.addRow("Creado:", self.created_label)

        self.updated_label = QLabel("--")
        info_layout.addRow("Actualizado:", self.updated_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Error message section (always present)
        self.error_group = QGroupBox("Mensaje de Error")
        self.error_group.setVisible(False)  # Hidden by default

        error_layout = QVBoxLayout()
        self.error_text = QTextEdit()
        self.error_text.setMaximumHeight(100)
        self.error_text.setReadOnly(True)
        self.error_text.setText("")
        self.error_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #1a1a1a;
                color: #ff6b6b;
                border: 1px solid #ff6b6b;
                border-radius: 4px;
                padding: 8px;
                font-family: monospace;
            }
        """
        )
        error_layout.addWidget(self.error_text)

        self.error_group.setLayout(error_layout)
        self.error_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ff6b6b;
                border-radius: 5px;
                margin-top: 1ex;
                color: #ff6b6b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ff6b6b;
            }
        """
        )
        layout.addWidget(self.error_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.retry_button = QPushButton("Reintentar")
        button_layout.addWidget(self.retry_button)

        self.cancel_button = QPushButton("Cancelar")
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)


class JobDetailsDialogLogic(JobDetailsDialogUI):
    """Dialog logic class - inherits UI and adds business logic."""

    def __init__(self, job: BurnJob, parent=None):
        # Initialize the UI base class first
        super().__init__(job, parent)

        # Store reference to parent for job queue access
        self.parent_window = parent

        # Then add business logic and initial data
        self.update_job_details()

        # Connect to parent for updates if available
        if parent:
            # Connect to job update signal from parent
            parent.job_updated.connect(self.on_job_updated_from_parent)

        # Connect retry button
        self.retry_button.clicked.connect(self.on_retry_clicked)

        # Connect cancel button
        self.cancel_button.clicked.connect(self.on_cancel_clicked)

    def on_cancel_clicked(self):
        """Handle cancel button click."""
        if not self.parent_window:
            return

        # Get job queue from parent window
        job_queue = getattr(self.parent_window, "job_queue", None)
        if not job_queue:
            return

        # Cancel the job
        success = job_queue.cancel_job(self.job.id)

        if success:
            # Update dialog with new job state
            self.update_job_details()
            # Show confirmation message
            QMessageBox.information(
                self,
                "Trabajo Cancelado",
                f"El trabajo {self.job.id[:8]}... ha sido cancelado exitosamente.",
            )
            # Close dialog since job is now cancelled
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Cancelación Fallida",
                "No se pudo cancelar el trabajo. Puede que ya esté completado o en un estado que no permite cancelación.",
            )

    def on_retry_clicked(self):
        """Handle retry button click."""
        if not self.parent_window:
            return

        # Get job queue from parent window
        job_queue = getattr(self.parent_window, "job_queue", None)
        if not job_queue:
            return

        # Retry the job
        success = job_queue.retry_job(self.job.id)

        if success:
            # Update dialog with new job state
            self.update_job_details()
            # Close dialog since job is now pending again
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Reintento Fallido",
                "No se pudo reintentar el trabajo.",
            )

    def on_job_updated_from_parent(self, job: BurnJob):
        """Handle job updates from parent window."""
        if job.id == self.job_id:
            self.job = job
            self.update_job_details()

    def update_job_details(self, job: Optional[BurnJob] = None):
        """Update the dialog with job details."""
        if job:
            self.job = job

        # Update labels
        if self.job_id_txt.text() != self.job.id:
            self.job_id_txt.setText(self.job.id)

        self.status_label.setText(self.job.status.value.title())
        self.filename_label.setText(self.job.iso_info.get("filename", "Unknown"))

        # Disc type
        disc_type_text = self.job.disc_type if self.job.disc_type else "No detectado"
        self.disc_type_label.setText(disc_type_text)

        # Color code disc type in details dialog
        if self.job.disc_type == "CD":
            self.disc_type_label.setStyleSheet("color: #0066cc; font-weight: bold;")  # Blue for CD
        elif self.job.disc_type == "DVD":
            self.disc_type_label.setStyleSheet(
                "color: #006600; font-weight: bold;"
            )  # Green for DVD
        elif self.job.disc_type == "Invalid":
            self.disc_type_label.setStyleSheet(
                "color: #cc0000; font-weight: bold;"
            )  # Red for invalid
        else:
            self.disc_type_label.setStyleSheet(
                "color: #666666; font-weight: bold;"
            )  # Gray for unknown

        # Patient information
        study_info = self.job.iso_info.get("study", {})
        patient_info = study_info.get("patient", {})
        patient_name = patient_info.get("fullName", "Desconocido")
        patient_id = patient_info.get("identifier", "N/A")
        self.patient_label.setText(f"{patient_name} (ID: {patient_id})")

        # Study information
        study_desc = study_info.get("dicomDescription") or "Sin descripción"
        self.study_label.setText(f"{study_desc[:50]}..." if len(study_desc) > 50 else study_desc)

        self.progress_label.setText(f"{self.job.progress:.1f}%")
        self.created_label.setText(self.job.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        self.updated_label.setText(self.job.updated_at.strftime("%Y-%m-%d %H:%M:%S"))

        # Update progress bar
        self.progress_bar.setValue(int(self.job.progress))

        # Color code progress bar
        if self.job.status == JobStatus.COMPLETED:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #90EE90; }")
        elif self.job.status == JobStatus.FAILED:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #FFB6C1; }")
        else:
            self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ADD8E6; }")

        # Update button states
        # Get max retries from parent window's config if available
        max_retries = 2  # default
        if self.parent_window and hasattr(self.parent_window, "config"):
            max_retries = self.parent_window.config.max_retries

        self.retry_button.setEnabled(
            self.job.status in [JobStatus.FAILED, JobStatus.COMPLETED, JobStatus.CANCELLED]
            and self.job.retry_count < max_retries
        )
        self.cancel_button.setEnabled(
            self.job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        )

        # Update error message section
        self.update_error_section()

    def update_error_section(self):
        """Update the error message section visibility and content."""
        if self.job.error_message:
            # Show error section and update content
            self.error_group.setVisible(True)
            self.error_text.setText(self.job.error_message)
        else:
            # Hide error section when no error
            self.error_group.setVisible(False)
            self.error_text.setText("")


# JobDetailsDialogLogic is the complete dialog class that combines UI and Logic
JobDetailsDialog = JobDetailsDialogLogic
