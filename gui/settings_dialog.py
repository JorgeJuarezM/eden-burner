"""
Settings dialog for EPSON PP-100 Disc Burner Application
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from config import Config


class SettingsDialog(QDialog):
    """Settings dialog with tabbed interface for configuration management."""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.modified_settings = {}

        self.setWindowTitle("Configuración - EPSON PP-100 Disc Burner")
        self.setModal(True)
        self.resize(700, 600)

        self.setup_ui()
        self.load_current_settings()

        self.setStyleSheet(
            """
                * {
                    background-color: black;
                }
            """
        )

    def setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: black; /* Default tab background */
                color: white;
                border: 1px solid white;
                padding: 10px;
            }
            QTabBar::tab:selected {
                background-color: darkgray; /* Selected tab background */
            }
            QTabBar::tab:hover {
                background-color: #212121; /* Tab background on hover */
            }

            QLineEdit,
            QComboBox,
            QSpinBox {
                padding: 5px;
                border: 1px solid #212121;
            }
            QGroupBox {
                padding: 10px;
            }
            """
        )

        # Create tabs
        self.create_general_tab()
        self.create_folders_tab()
        self.create_robot_tab()
        self.create_jobs_tab()
        self.create_interface_tab()
        self.create_database_tab()

        layout.addWidget(self.tab_widget)

        # Create buttons
        buttons_layout = QHBoxLayout()

        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """
        )

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def create_general_tab(self):
        """Create General settings tab."""
        tab = QWidget()
        tab.setStyleSheet(
            """
            margin: 5px;
            """
        )

        layout = QFormLayout(tab)
        layout.setSpacing(20)

        # API Endpoint
        self.api_endpoint_edit = QLineEdit()
        self.api_endpoint_edit.setPlaceholderText("http://localhost:8000/graphql-middleware/")
        layout.addRow("API Endpoint:", self.api_endpoint_edit)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Ingrese API key")
        layout.addRow("API Key:", self.api_key_edit)

        # API Timeout
        self.api_timeout_combo = QComboBox()
        self.api_timeout_combo.addItems(
            ["30 segundos", "60 segundos", "90 segundos", "120 segundos"]
        )
        layout.addRow("API Timeout:", self.api_timeout_combo)

        # Robot UUID
        self.robot_uuid_edit = QLineEdit()
        self.robot_uuid_edit.setPlaceholderText("00000000-0000-0000-0000-000000000000")
        layout.addRow("Robot UUID:", self.robot_uuid_edit)

        self.tab_widget.addTab(tab, "General")

    def create_folders_tab(self):
        """Create Folders settings tab."""
        tab = QWidget()

        # Create scroll area for better layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Downloads folder
        downloads_layout = QHBoxLayout()
        self.downloads_edit = QLineEdit()
        self.downloads_edit.setPlaceholderText("Seleccione carpeta de descargas")
        downloads_button = QPushButton("...")
        downloads_button.clicked.connect(lambda: self.select_folder(self.downloads_edit))
        downloads_layout.addWidget(self.downloads_edit)
        downloads_layout.addWidget(downloads_button)

        downloads_group = QGroupBox("Carpeta de Descargas")
        downloads_group.setLayout(downloads_layout)
        layout.addWidget(downloads_group)

        # JDF Files folder
        jdf_layout = QHBoxLayout()
        self.jdf_edit = QLineEdit()
        self.jdf_edit.setPlaceholderText("Seleccione carpeta de archivos JDF")
        jdf_button = QPushButton("...")
        jdf_button.clicked.connect(lambda: self.select_folder(self.jdf_edit))
        jdf_layout.addWidget(self.jdf_edit)
        jdf_layout.addWidget(jdf_button)

        jdf_group = QGroupBox("Carpeta de Archivos JDF")
        jdf_group.setLayout(jdf_layout)
        layout.addWidget(jdf_group)

        # Completed folder
        completed_layout = QHBoxLayout()
        self.completed_edit = QLineEdit()
        self.completed_edit.setPlaceholderText("Seleccione carpeta de completados")
        completed_button = QPushButton("...")
        completed_button.clicked.connect(lambda: self.select_folder(self.completed_edit))
        completed_layout.addWidget(self.completed_edit)
        completed_layout.addWidget(completed_button)

        completed_group = QGroupBox("Carpeta de Completados")
        completed_group.setLayout(completed_layout)
        layout.addWidget(completed_group)

        # Failed folder
        failed_layout = QHBoxLayout()
        self.failed_edit = QLineEdit()
        self.failed_edit.setPlaceholderText("Seleccione carpeta de fallidos")
        failed_button = QPushButton("...")
        failed_button.clicked.connect(lambda: self.select_folder(self.failed_edit))
        failed_layout.addWidget(self.failed_edit)
        failed_layout.addWidget(failed_button)

        failed_group = QGroupBox("Carpeta de Fallidos")
        failed_group.setLayout(failed_layout)
        layout.addWidget(failed_group)

        # Temp folder
        temp_layout = QHBoxLayout()
        self.temp_edit = QLineEdit()
        self.temp_edit.setPlaceholderText("Seleccione carpeta temporal")
        temp_button = QPushButton("...")
        temp_button.clicked.connect(lambda: self.select_folder(self.temp_edit))
        temp_layout.addWidget(self.temp_edit)
        temp_layout.addWidget(temp_button)

        temp_group = QGroupBox("Carpeta Temporal")
        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)

        layout.addStretch()
        scroll.setWidget(widget)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "Carpetas")

    def create_robot_tab(self):
        """Create Robot settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Robot UUID (duplicate from general, but keeping here for convenience)
        robot_layout = QFormLayout()

        self.robot_uuid_edit2 = QLineEdit()
        self.robot_uuid_edit2.setPlaceholderText("00000000-0000-0000-0000-000000000000")
        robot_layout.addRow("Robot UUID:", self.robot_uuid_edit2)

        robot_group = QGroupBox("Configuración del Robot")
        robot_group.setLayout(robot_layout)
        layout.addWidget(robot_group)

        # Template files
        templates_layout = QVBoxLayout()

        # JDF Template
        jdf_template_layout = QHBoxLayout()
        self.jdf_template_edit = QLineEdit()
        self.jdf_template_edit.setPlaceholderText("Seleccione archivo plantilla JDF")
        jdf_template_button = QPushButton("...")
        jdf_template_button.clicked.connect(
            lambda: self.select_file(self.jdf_template_edit, "JDF Files (*.jdf)")
        )
        jdf_template_layout.addWidget(self.jdf_template_edit)
        jdf_template_layout.addWidget(jdf_template_button)

        templates_layout.addLayout(jdf_template_layout)

        # Label file
        label_layout = QHBoxLayout()
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("Seleccione archivo de etiqueta TDD")
        label_button = QPushButton("...")
        label_button.clicked.connect(lambda: self.select_file(self.label_edit, "TDD Files (*.tdd)"))
        label_layout.addWidget(self.label_edit)
        label_layout.addWidget(label_button)

        templates_layout.addLayout(label_layout)

        # Data template
        data_layout = QHBoxLayout()
        self.data_template_edit = QLineEdit()
        self.data_template_edit.setPlaceholderText("Seleccione archivo plantilla de datos")
        data_button = QPushButton("...")
        data_button.clicked.connect(
            lambda: self.select_file(self.data_template_edit, "All Files (*)")
        )
        data_layout.addWidget(self.data_template_edit)
        data_layout.addWidget(data_button)

        templates_layout.addLayout(data_layout)

        templates_group = QGroupBox("Archivos de Plantilla")
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Robot")

    def create_jobs_tab(self):
        """Create Jobs settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Max concurrent jobs
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        layout.addRow("Trabajos Concurrentes Máximos:", self.max_concurrent_spin)

        # Check interval
        self.check_interval_combo = QComboBox()
        self.check_interval_combo.addItems(
            ["10 segundos", "30 segundos", "1 minuto", "5 minutos", "10 minutos"]
        )
        layout.addRow("Intervalo de Verificación:", self.check_interval_combo)

        # Retry failed jobs
        self.retry_failed_check = QCheckBox("Reintentar trabajos fallidos")
        layout.addRow(self.retry_failed_check)

        # Max retries
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        layout.addRow("Máximo de Reintentos:", self.max_retries_spin)

        self.tab_widget.addTab(tab, "Trabajos")

    def create_interface_tab(self):
        """Create Interface settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # GUI settings
        gui_layout = QFormLayout()

        # Refresh interval
        self.refresh_interval_combo = QComboBox()
        self.refresh_interval_combo.addItems(
            ["1 segundo", "2 segundos", "5 segundos", "10 segundos"]
        )
        gui_layout.addRow("Intervalo de Actualización GUI:", self.refresh_interval_combo)

        # Show notifications
        self.show_notifications_check = QCheckBox("Mostrar notificaciones del sistema")
        gui_layout.addRow(self.show_notifications_check)

        gui_group = QGroupBox("Configuración de Interfaz")
        gui_group.setLayout(gui_layout)
        layout.addWidget(gui_group)

        # Logging settings
        logging_layout = QFormLayout()

        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        logging_layout.addRow("Nivel de Log:", self.log_level_combo)

        # Log file
        log_file_layout = QHBoxLayout()
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setPlaceholderText("Seleccione archivo de log")
        log_file_button = QPushButton("...")
        log_file_button.clicked.connect(
            lambda: self.select_file(self.log_file_edit, "Log Files (*.log);;All Files (*)")
        )
        log_file_layout.addWidget(self.log_file_edit)
        log_file_layout.addWidget(log_file_button)

        logging_layout.addRow("Archivo de Log:", log_file_layout)

        # Max log size
        self.log_max_size_spin = QSpinBox()
        self.log_max_size_spin.setRange(1, 1000)
        self.log_max_size_spin.setSuffix(" MB")
        logging_layout.addRow("Tamaño Máximo de Log:", self.log_max_size_spin)

        logging_group = QGroupBox("Configuración de Logging")
        logging_group.setLayout(logging_layout)
        layout.addWidget(logging_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Interfaz")

    def create_database_tab(self):
        """Create Database settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # Database file
        db_layout = QHBoxLayout()
        self.database_file_edit = QLineEdit()
        self.database_file_edit.setPlaceholderText("Seleccione archivo de base de datos")
        db_button = QPushButton("...")
        db_button.clicked.connect(
            lambda: self.select_file(self.database_file_edit, "SQLite Files (*.db);;All Files (*)")
        )
        db_layout.addWidget(self.database_file_edit)
        db_layout.addWidget(db_button)

        layout.addRow("Archivo de Base de Datos:", db_layout)

        # Backup count
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 20)
        layout.addRow("Número de Backups:", self.backup_count_spin)

        self.tab_widget.addTab(tab, "Base de Datos")

    def load_current_settings(self):
        """Load current configuration values into form fields."""
        # General tab
        self.api_endpoint_edit.setText(self.config.graphql_endpoint)
        self.api_key_edit.setText(self.config.api_key)

        # Set API timeout in combobox (convert seconds to index)
        timeout_options = [30, 60, 90, 120]
        current_timeout = self.config.api_timeout
        if current_timeout in timeout_options:
            index = timeout_options.index(current_timeout)
            self.api_timeout_combo.setCurrentIndex(index)
        else:
            # If current value is not in our options, set to first option
            self.api_timeout_combo.setCurrentIndex(0)

        self.robot_uuid_edit.setText(self.config.robot_uuid)
        self.robot_uuid_edit2.setText(self.config.robot_uuid)

        # Folders tab
        self.downloads_edit.setText(str(self.config.downloads_folder))
        self.jdf_edit.setText(str(self.config.jdf_folder))
        self.completed_edit.setText(str(self.config.completed_folder))
        self.failed_edit.setText(str(self.config.failed_folder))
        self.temp_edit.setText(str(self.config.temp_folder))

        # Robot tab
        self.jdf_template_edit.setText(self.config.jdf_template)
        self.label_edit.setText(self.config.label_file)
        self.data_template_edit.setText(self.config.data_template)

        # Jobs tab
        self.max_concurrent_spin.setValue(self.config.max_concurrent_jobs)

        # Set check interval in combobox (convert seconds to index)
        check_interval_options = [10, 30, 60, 300, 600]  # seconds
        current_check_interval = self.config.check_interval
        if current_check_interval in check_interval_options:
            index = check_interval_options.index(current_check_interval)
            self.check_interval_combo.setCurrentIndex(index)
        else:
            # If current value is not in our options, set to first option (10 seconds)
            self.check_interval_combo.setCurrentIndex(0)

        self.retry_failed_check.setChecked(self.config.retry_failed_jobs)
        self.max_retries_spin.setValue(self.config.max_retries)

        # Interface tab
        # Set refresh interval in combobox (convert ms to index)
        refresh_interval_options = [1000, 2000, 5000, 10000]  # milliseconds
        current_refresh_interval = self.config.gui_refresh_interval
        if current_refresh_interval in refresh_interval_options:
            index = refresh_interval_options.index(current_refresh_interval)
            self.refresh_interval_combo.setCurrentIndex(index)
        else:
            # If current value is not in our options, set to first option (1 second)
            self.refresh_interval_combo.setCurrentIndex(0)

        self.show_notifications_check.setChecked(self.config.show_notifications)
        self.log_level_combo.setCurrentText(self.config.config_data["logging"]["level"])
        self.log_file_edit.setText(self.config.config_data["logging"]["file"])
        self.log_max_size_spin.setValue(
            self.config.config_data["logging"]["max_size"] // (1024 * 1024)
        )

        # Database tab
        self.database_file_edit.setText(str(self.config.database_file))
        self.backup_count_spin.setValue(self.config.database_backup_count)

    def select_folder(self, edit_widget):
        """Open folder selection dialog."""
        current_path = edit_widget.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta", current_path)
        if folder:
            edit_widget.setText(folder)

    def select_file(self, edit_widget, file_filter):
        """Open file selection dialog."""
        current_path = edit_widget.text() or str(Path.home())
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo", current_path, file_filter
        )
        if file_path:
            edit_widget.setText(file_path)

    def save_settings(self):
        """Save settings to configuration."""
        try:
            # General tab
            self.config.graphql_endpoint = self.api_endpoint_edit.text().strip()
            self.config.api_key = self.api_key_edit.text().strip()

            # Convert combobox index to seconds
            timeout_options = [30, 60, 90, 120]
            selected_index = self.api_timeout_combo.currentIndex()
            self.config.config_data["api"]["timeout"] = (
                timeout_options[selected_index] if selected_index >= 0 else 30
            )

            self.config.config_data["robot"]["robot_uuid"] = self.robot_uuid_edit.text().strip()

            # Folders tab
            self.config.config_data["folders"]["downloads"] = self.downloads_edit.text().strip()
            self.config.config_data["folders"]["jdf_files"] = self.jdf_edit.text().strip()
            self.config.config_data["folders"]["completed"] = self.completed_edit.text().strip()
            self.config.config_data["folders"]["failed"] = self.failed_edit.text().strip()
            self.config.config_data["folders"]["temp"] = self.temp_edit.text().strip()

            # Robot tab
            self.config.config_data["robot"]["jdf_template"] = self.jdf_template_edit.text().strip()
            self.config.config_data["robot"]["label_file"] = self.label_edit.text().strip()
            self.config.config_data["robot"][
                "data_template"
            ] = self.data_template_edit.text().strip()

            # Jobs tab
            self.config.config_data["jobs"]["max_concurrent"] = self.max_concurrent_spin.value()

            # Convert combobox index to seconds for check interval
            check_interval_options = [10, 30, 60, 300, 600]  # seconds
            check_selected_index = self.check_interval_combo.currentIndex()
            self.config.config_data["jobs"]["check_interval"] = (
                check_interval_options[check_selected_index] if check_selected_index >= 0 else 10
            )

            self.config.config_data["jobs"]["retry_failed"] = self.retry_failed_check.isChecked()
            self.config.config_data["jobs"]["max_retries"] = self.max_retries_spin.value()

            # Interface tab
            # Convert combobox index to milliseconds for refresh interval
            refresh_interval_options = [1000, 2000, 5000, 10000]  # milliseconds
            refresh_selected_index = self.refresh_interval_combo.currentIndex()
            self.config.config_data["gui"]["refresh_interval"] = (
                refresh_interval_options[refresh_selected_index]
                if refresh_selected_index >= 0
                else 1000
            )

            self.config.config_data["gui"][
                "show_notifications"
            ] = self.show_notifications_check.isChecked()
            self.config.config_data["logging"]["level"] = self.log_level_combo.currentText()
            self.config.config_data["logging"]["file"] = self.log_file_edit.text().strip()
            self.config.config_data["logging"]["max_size"] = (
                self.log_max_size_spin.value() * 1024 * 1024
            )

            # Database tab
            self.config.config_data["database"]["file"] = self.database_file_edit.text().strip()
            self.config.config_data["database"]["backup_count"] = self.backup_count_spin.value()

            # Save configuration
            self.config.save_config()

            QMessageBox.information(
                self, "Configuración Guardada", "La configuración se ha guardado exitosamente."
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar la configuración:\n{str(e)}")

    def get_modified_settings_summary(self):
        """Get summary of modified settings."""
        summary = []

        # Check each setting for changes
        if self.api_endpoint_edit.text().strip() != self.config.graphql_endpoint:
            summary.append(f"API Endpoint: {self.api_endpoint_edit.text().strip()}")

        if self.api_key_edit.text().strip() != self.config.api_key:
            summary.append("API Key: [modificado]")

        # Check API timeout (convert combobox index to seconds)
        timeout_options = [30, 60, 90, 120]
        selected_index = self.api_timeout_combo.currentIndex()
        current_timeout_value = timeout_options[selected_index] if selected_index >= 0 else 30

        if current_timeout_value != self.config.api_timeout:
            summary.append(f"API Timeout: {current_timeout_value}s")

        # Check check interval (convert combobox index to seconds)
        check_interval_options = [10, 30, 60, 300, 600]
        check_selected_index = self.check_interval_combo.currentIndex()
        current_check_value = (
            check_interval_options[check_selected_index] if check_selected_index >= 0 else 10
        )

        if current_check_value != self.config.check_interval:
            summary.append(f"Intervalo de Verificación: {current_check_value}s")

        # Check refresh interval (convert combobox index to milliseconds)
        refresh_interval_options = [1000, 2000, 5000, 10000]
        refresh_selected_index = self.refresh_interval_combo.currentIndex()
        current_refresh_value = (
            refresh_interval_options[refresh_selected_index]
            if refresh_selected_index >= 0
            else 1000
        )

        if current_refresh_value != self.config.gui_refresh_interval:
            summary.append(f"Intervalo de Actualización GUI: {current_refresh_value}ms")

        if self.robot_uuid_edit.text().strip() != self.config.robot_uuid:
            summary.append(f"Robot UUID: {self.robot_uuid_edit.text().strip()}")

        # Add more checks for other settings...

        return summary
