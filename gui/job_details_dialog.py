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
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from job_queue import BurnJob, JobStatus


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
                background-color: #2d2d2d;
            }
            QLabel {
                color: #ffffff;
            }
            QGroupBox {
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #ffffff;
                background-color: #2d2d2d;
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

        # Error message group (if any)
        self.error_group = None
        self.error_text = None

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

        # Then add business logic and initial data
        self.update_job_details()

        # Connect to parent for updates if available
        if parent:
            # Connect to job update signal from parent
            parent.job_updated.connect(self.on_job_updated_from_parent)

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

        # Patient information
        study_info = self.job.iso_info.get("study", {})
        patient_info = study_info.get("patient", {})
        patient_name = patient_info.get("fullName", "Desconocido")
        patient_id = patient_info.get("identifier", "N/A")
        self.patient_label.setText(f"{patient_name} (ID: {patient_id})")

        # Study information
        study_desc = study_info.get("dicomDescription", "Sin descripción")
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
        self.retry_button.setEnabled(self.job.status == JobStatus.FAILED)
        self.cancel_button.setEnabled(
            self.job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        )

        # Update error message section
        self.update_error_section()

        # Update history
        self.history_text.clear()
        self.history_text.append(
            f"Trabajo creado: {self.job.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        if self.job.error_message:
            self.history_text.append(f"Error: {self.job.error_message}")

    def update_error_section(self):
        """Update the error message section."""
        # Remove existing error group if present
        if self.error_group:
            self.error_group.setParent(None)
            self.error_group.deleteLater()
            self.error_group = None
            self.error_text = None

        # Add error group if there's an error message
        if self.job.error_message:
            error_group = QGroupBox("Mensaje de Error")
            error_layout = QVBoxLayout()

            error_text = QTextEdit()
            error_text.setMaximumHeight(100)
            error_text.setReadOnly(True)
            error_text.setText(self.job.error_message)
            error_layout.addWidget(error_text)

            error_group.setLayout(error_layout)

            # Insert error group before history group
            layout = self.layout()
            layout.insertWidget(layout.count() - 2, error_group)  # Insert before buttons

            self.error_group = error_group
            self.error_text = error_text


# JobDetailsDialogLogic is the complete dialog class that combines UI and Logic
JobDetailsDialog = JobDetailsDialogLogic
