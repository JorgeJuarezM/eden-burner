# ============================================================================
# Makefile - EPSON PP-100 Disc Burner Application
# ============================================================================
# Este archivo contiene objetivos para tareas comunes de desarrollo y mantenimiento
# del proyecto de quemado de discos con robot EPSON PP-100.
#
# Uso típico:
#   make format      - Formatear código según estándares
#   make clean-db    - Limpiar base de datos y archivos generados
#   make help        - Mostrar esta ayuda
#
# ============================================================================

# ============================================================================
# FORMATEO DE CÓDIGO
# ============================================================================
# Ejecuta herramientas de calidad de código para formatear y limpiar el código
# fuente según estándares definidos (black, isort, flake8, etc.)
#
# Uso: make format
# Efecto: Aplica formateo automático a todos los archivos Python
# ============================================================================
format:
	python scripts/code_quality.py clean

# ============================================================================
# LIMPIEZA DE ARCHIVOS Y BASE DE DATOS
# ============================================================================
# Limpia completamente el entorno de desarrollo eliminando:
# - Base de datos SQLite con trabajos y configuración
# - Archivos de distribución (dist/)
# - Archivos de construcción (build/)
# - Archivos JDF generados (jdf_files/)
#
# ⚠️  CUIDADO: Esta operación elimina datos permanentemente
#    - Se perderán todos los trabajos registrados
#    - Se perderá el historial de quemado
#    - Se perderán configuraciones personalizadas
#
# Uso: make clean-db
# Efecto: Limpieza completa del entorno de desarrollo
# ============================================================================
clean-db:
	python main.py --clear-database
	rm -dfr dist/
	rm -dfr build/
	rm -dfr jdf_files/*.*

# ============================================================================
# AYUDA Y DOCUMENTACIÓN
# ============================================================================
# Muestra información de ayuda sobre los objetivos disponibles
#
# Uso: make help
# ============================================================================
help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                    EPSON PP-100 Disc Burner                    ║"
	@echo "║                     Makefile - Ayuda                           ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Objetivos disponibles:"
	@echo ""
	@echo "  make format     - Formatear código según estándares de calidad"
	@echo "  make clean-db   - Limpiar base de datos y archivos generados"
	@echo "  make help       - Mostrar esta ayuda"
	@echo ""
	@echo "Para más información, consulte la documentación en docs/":
	@echo "  - Guía de Desarrollo:     docs/DEVELOPMENT_README.md"
	@echo "  - Guía de Construcción:   docs/BUILD_README.md"
	@echo "  - Guía de Plantillas:     docs/TEMPLATES_README.md"
	@echo ""

# ============================================================================
# DECLARACIÓN DE OBJETIVOS FALSOS
# ============================================================================
# Estos objetivos no generan archivos físicos, sino que ejecutan acciones
.PHONY: format clean-db help