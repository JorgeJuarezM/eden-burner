"""
PyQt GUI for EPSON PP-100 Disc Burner Application - Main Window
"""

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.job_queue import BurnJob, JobQueue, JobStatus
from config import Config
from gui.job_details_dialog import JobDetailsDialog
from gui.job_table_widget import JobTableWidget
from gui.settings_dialog import SettingsDialog


class MainWindowUI(QMainWindow):
    """Main window UI class - handles only PyQt design and widget creation."""

    def __init__(self, config: Config, job_queue: JobQueue):
        super().__init__()
        self.config = config
        self.job_queue = job_queue

        # Initialize UI only
        self.setup_ui()

    def setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle("EPSON PP-100 Disc Burner")
        self.setFixedSize(1024, 768)

        # Apply Eden-themed dark styles (black and white theme)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #000000;
                color: #ffffff;
            }
            QWidget {
                background-color: #000000;
                color: #ffffff;
            }
            QMenuBar {
                background-color: #1a1a1a;
                color: #ffffff;
                border-bottom: 1px solid #333333;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #333333;
            }
            QMenu {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #333333;
            }
            QStatusBar {
                background-color: #1a1a1a;
                color: #ffffff;
                border-top: 1px solid #333333;
            }
            QComboBox {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #333333;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                selection-background-color: #333333;
            }
            QPushButton {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
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
            QGroupBox {
                color: #ffffff;
                border: 2px solid #333333;
                border-radius: 5px;
                margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #ffffff;
                background-color: #000000;
            }
        """
        )

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)

        # Create main content area (table takes full width)
        self.main_content = self.create_main_content()
        layout.addWidget(self.main_content)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Menu bar
        self.setup_menu_bar()

    def create_main_content(self):
        """Create the main content area with header and job table."""
        # Create central widget with header and job table
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(8, 8, 8, 8)  # Smaller margins
        layout.setSpacing(8)  # Reduced spacing

        # Add header with logo and title
        header_panel = self.create_header_panel()
        layout.addWidget(header_panel)

        # Job table panel takes remaining space
        job_panel = self.create_job_list_panel()
        layout.addWidget(job_panel)

        return central_widget

    def create_header_panel(self):
        """Create the header panel with logo and title."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)  # No margins in header
        layout.setSpacing(12)  # Small spacing between elements

        # Logo on the left (small and compact)
        logo_label = QLabel()
        logo_pixmap = QPixmap("assets/logo.png")
        logo_label.setPixmap(logo_pixmap)

        # Add subtle styling to logo container
        logo_label.setStyleSheet(
            """
            QLabel {
                background-color: transparent;
                padding: 4px;
                border-radius: 4px;
            }
        """
        )

        layout.addWidget(logo_label)

        # Title to the right of the logo
        title_label = QLabel("EPSON PP-100 Disc Burner")
        title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                padding: 8px 0px;
            }
        """
        )

        layout.addWidget(title_label)
        layout.addStretch()  # Push everything to the left

        return panel

    def create_job_list_panel(self):
        """Create the job list panel with improved design."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)  # No margins
        layout.setSpacing(8)  # Reduced spacing

        # Title row with subtitle and filter buttons
        title_row_layout = QHBoxLayout()
        title_row_layout.setContentsMargins(0, 0, 0, 0)
        title_row_layout.setSpacing(8)

        # Compact panel title
        title_label = QLabel("Trabajos de Quemado")
        title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 0px;
            }
        """
        )
        title_row_layout.addWidget(title_label)

        # Spacer to push filter buttons to the right
        title_row_layout.addStretch()

        # Filter buttons with toggle effect
        self.create_filter_buttons(title_row_layout)

        layout.addLayout(title_row_layout)

        # Job table - no height limit to use full available space
        self.job_table = JobTableWidget()
        layout.addWidget(self.job_table)

        # Queue status
        self.queue_status_label = QLabel("Estado de la cola: --")
        layout.addWidget(self.queue_status_label)

        # Control buttons
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("Actualizar")
        button_layout.addWidget(self.refresh_button)

        self.clear_completed_button = QPushButton("Limpiar Completados")
        button_layout.addWidget(self.clear_completed_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        return panel

    def create_filter_buttons(self, layout):
        """Create filter buttons with toggle effect."""
        # Create button group for exclusive selection
        self.filter_button_group = QButtonGroup()
        self.filter_button_group.setExclusive(True)

        # Filter options
        filter_options = [
            ("Todos", "all", "🔍"),
            ("Pendientes", "pending", "⏳"),
            ("Descargando", "downloading", "📥"),
            ("Quemando", "burning", "🔥"),
            ("Completados", "completed", "✅"),
            ("Fallidos", "failed", "❌"),
        ]

        for text, value, icon in filter_options:
            button = QPushButton(f"{icon} {text}")
            button.setCheckable(True)
            button.setProperty("filter_value", value)

            # Default styling
            button.setStyleSheet(
                """
                QPushButton {
                    background-color: #333333;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    margin: 0px 2px;
                }
                QPushButton:hover {
                    background-color: #444444;
                    border-color: #666666;
                }
                QPushButton:checked {
                    background-color: #1976D2;
                    border-color: #1976D2;
                    color: #ffffff;
                }
                QPushButton:checked:hover {
                    background-color: #1565C0;
                }
            """
            )

            # Connect signal
            button.clicked.connect(lambda checked, v=value: self.on_filter_changed(v))

            # Add to button group
            self.filter_button_group.addButton(button)
            layout.addWidget(button)

            # Set "Todos" as default selected
            if value == "all":
                button.setChecked(True)
                self.current_filter = "all"

    def setup_menu_bar(self):
        """Setup the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("Archivo")

        settings_action = QAction("Configuración", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Herramientas")

        test_api_action = QAction("Probar Conexión API", self)
        test_api_action.triggered.connect(self.test_api_connection)
        tools_menu.addAction(test_api_action)

        # Help menu
        help_menu = menubar.addMenu("Ayuda")

        about_action = QAction("Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def connect_menu_actions(self):
        """Connect menu actions to their corresponding methods."""
        # Menu actions are already connected in setup_menu_bar
        # This method is here for potential future menu action connections


class MainWindowLogic(MainWindowUI):
    """Main window logic class - inherits UI and adds business logic."""

    # Signals
    job_updated = pyqtSignal(object)  # BurnJob
    job_completed = pyqtSignal(str)  # job_id
    job_failed = pyqtSignal(str)  # job_id

    def __init__(self, config: Config, job_queue: JobQueue):
        # Initialize the UI base class first
        super().__init__(config, job_queue)

        # Then add business logic
        self.setup_connections()
        self.setup_timers()

        # Load initial data
        self.refresh_data()

        # Connect UI signals to logic methods
        self.job_table.itemDoubleClicked.connect(self.on_job_double_clicked)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.clear_completed_button.clicked.connect(self.clear_completed_jobs)

        # Connect menu actions
        self.connect_menu_actions()

    def setup_connections(self):
        """Setup signal connections."""
        # Connect job queue signals
        self.job_queue.add_job_update_callback(self.on_job_updated)

    def on_job_updated(self, job: BurnJob):
        """Handle job update signal."""
        self.job_updated.emit(job)
        self.refresh_job_display()

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

    def on_filter_changed(self, filter_value):
        """Handle filter change."""
        self.current_filter = filter_value
        self.refresh_job_display()

    def refresh_data(self):
        """Refresh all displayed data."""
        self.refresh_job_display()
        self.update_status_bar()

    def on_job_double_clicked(self, item):
        """Handle double click on job item."""
        if item is None:
            return

        try:
            row = item.row()
            job_id_item = self.job_table.item(row, 0)

            if job_id_item:
                job_id = job_id_item.toolTip()  # Get full job ID from tooltip

                if job_id:
                    job = self.job_queue.get_job(job_id)
                    if job:
                        # Open job details dialog
                        dialog = JobDetailsDialog(job, self)
                        dialog.exec_()
                    else:
                        QMessageBox.warning(
                            self,
                            "Trabajo no encontrado",
                            f"No se pudo encontrar el trabajo con ID: {job_id}",
                        )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al procesar doble clic: {e}")

    def refresh_job_display(self):
        """Refresh the job table display."""
        filter_status = getattr(self, "current_filter", "all")

        if filter_status == "all":
            jobs = self.job_queue.get_all_jobs()
        else:
            # Map filter to status
            status_map = {
                "pending": JobStatus.PENDING,
                "downloading": JobStatus.DOWNLOADING,
                "burning": JobStatus.BURNING,
                "completed": JobStatus.COMPLETED,
                "failed": JobStatus.FAILED,
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

    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.exec_()

    def test_api_connection(self):
        """Test API connection."""
        try:
            # This would use the job queue's download manager to test connection
            QMessageBox.information(
                self, "Prueba de conexión", "Prueba de conexión no implementada aún."
            )
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
            "Versión 1.0",
        )

    def clear_completed_jobs(self):
        """Clear completed jobs from display and storage."""
        try:
            # Ask for confirmation
            reply = QMessageBox.question(
                self,
                "Confirmar limpieza",
                "¿Está seguro de que desea limpiar los trabajos completados?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                # This would clean up completed jobs from storage
                QMessageBox.information(self, "Limpieza", "Limpieza no implementada aún.")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error limpiando trabajos: {e}")


# MainWindowLogic is the complete window class that combines UI and Logic
MainWindow = MainWindowLogic
