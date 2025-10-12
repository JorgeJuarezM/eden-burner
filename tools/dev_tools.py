#!/usr/bin/env python3
"""
Development utilities for EPSON PP-100 Disc Burner
Provides debugging and development helpers
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_with_debugging():
    """Run the application with debugging enabled."""
    print("🔧 Running application with debugging...")

    env = os.environ.copy()
    env['EPSON_DEBUG'] = '1'
    env['PYTHONPATH'] = str(Path.cwd())

    cmd = [sys.executable, 'main.py', '--background']

    try:
        subprocess.run(cmd, env=env, check=True)
    except KeyboardInterrupt:
        print("\n✅ Application stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Application failed: {e}")

def test_configuration():
    """Test configuration loading and validation."""
    print("🔍 Testing configuration...")

    try:
        from config import Config

        config = Config()

        print("✅ Configuration loaded successfully")
        print(f"📁 Downloads folder: {config.downloads_folder}")
        print(f"📁 JDF folder: {config.jdf_folder}")
        print(f"🔗 API endpoint: {config.graphql_endpoint}")
        print(f"🤖 Robot name: {config.robot_name}")

        # Validate configuration
        errors = config.validate_config()
        if errors:
            print("⚠️ Configuration warnings:")
            for error in errors:
                print(f"  • {error}")
        else:
            print("✅ Configuration is valid")

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

def check_dependencies():
    """Check if all dependencies are installed."""
    print("📦 Checking dependencies...")

    required_modules = [
        'PyQt5', 'requests', 'gql', 'aiohttp', 'sqlalchemy',
        'pyyaml', 'schedule', 'python_dateutil'
    ]

    missing = []

    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            missing.append(module)

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies are installed")
        return True

def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")

    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', '.', '-v'
        ], capture_output=False, text=True)

        if result.returncode == 0:
            print("✅ All tests passed")
        else:
            print("❌ Some tests failed")
            print(result.stdout)

        return result.returncode == 0

    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False

def create_dev_config():
    """Create a development configuration file."""
    print("⚙️ Creating development configuration...")

    dev_config = '''# Configuración de desarrollo para EPSON PP-100 Disc Burner
# Este archivo contiene configuraciones específicas para desarrollo

# Configuración de API GraphQL (desarrollo)
api:
  graphql_endpoint: "https://develop.dev-land.space/graphql-middleware/"
  api_key: "89bb41a2a6090688c0ce2219a652ef677ed20c84"
  timeout: 30
  retry_attempts: 3

# Carpetas para desarrollo
folders:
  downloads: "downloads"
  jdf_files: "jdf_files"
  completed: "completed"
  failed: "failed"
  temp: "temp"

# Configuración del robot (desarrollo)
robot:
  name: "EPSON_PP_100_DEV"
  jdf_template: "default.jdf"
  burn_speed: "4x"
  verify_after_burn: false  # Deshabilitado para desarrollo rápido
  auto_eject: false

# Configuración de trabajos (desarrollo)
jobs:
  max_concurrent: 1  # Solo un trabajo para desarrollo
  check_interval: 60  # Verificar cada minuto
  retry_failed: true
  max_retries: 3

# Configuración de logging (desarrollo)
logging:
  level: "DEBUG"  # Nivel detallado para desarrollo
  file: "epson-burner-dev.log"
  max_size: 10485760  # 10MB
  backup_count: 3

# Configuración de interfaz gráfica (desarrollo)
gui:
  refresh_interval: 1  # Actualización rápida para desarrollo
  theme: "default"
  show_notifications: true

# Configuración específica de desarrollo
development:
  debug_mode: true
  auto_reload: true
  test_mode: false'''

    config_path = 'config.dev.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(dev_config)

    print(f"✅ Development configuration created: {config_path}")

def main():
    parser = argparse.ArgumentParser(description='Development utilities for EPSON Disc Burner')
    parser.add_argument('--run', action='store_true', help='Run application with debugging')
    parser.add_argument('--test-config', action='store_true', help='Test configuration loading')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--test', action='store_true', help='Run test suite')
    parser.add_argument('--create-dev-config', action='store_true', help='Create development configuration file')
    parser.add_argument('--check-code-quality', action='store_true', help='Check code quality tools')
    parser.add_argument('--format-code', action='store_true', help='Format code with Black and isort')
    parser.add_argument('--lint-code', action='store_true', help='Lint code with flake8 and mypy')
    parser.add_argument('--clean-imports', action='store_true', help='Remove unused imports')
    parser.add_argument('--run-all-quality-checks', action='store_true', help='Run all code quality checks')

    args = parser.parse_args()

    if args.run:
        run_with_debugging()
    elif args.test_config:
        test_configuration()
    elif args.check_deps:
        check_dependencies()
    elif args.test:
        run_tests()
    elif args.create_dev_config:
        create_dev_config()
    elif args.check_code_quality:
        check_code_quality()
    elif args.format_code:
        format_code()
    elif args.lint_code:
        lint_code()
    elif args.clean_imports:
        clean_imports()
    elif args.run_all_quality_checks:
        run_all_quality_checks()
    else:
        print("🔧 EPSON PP-100 Disc Burner - Development Tools")
        print("=" * 50)
        print("Available commands:")
        print("  --run                 Run application with debugging")
        print("  --test-config         Test configuration loading")
        print("  --check-deps          Check if all dependencies are installed")
        print("  --test                Run test suite")
        print("  --create-dev-config   Create development configuration file")
        print("  --check-code-quality  Check code quality tools")
        print("  --format-code         Format code with Black and isort")
        print("  --lint-code           Lint code with flake8 and mypy")
        print("  --clean-imports       Remove unused imports")
        print("  --run-all-quality-checks  Run all code quality checks")
        print("\n💡 Use VS Code with .vscode/launch.json for full debugging support")

def check_code_quality():
    """Check if all development tools for code quality are installed."""
    print("🔍 Checking code quality tools...")

    required_tools = [
        ("black", "Black code formatter"),
        ("isort", "Import sorter"),
        ("flake8", "Python linter"),
        ("mypy", "Static type checker")
    ]

    missing_tools = []
    for tool, description in required_tools:
        if not _is_tool_installed(tool):
            missing_tools.append(f"{tool} ({description})")

    if missing_tools:
        print("❌ Missing code quality tools:")
        for tool in missing_tools:
            print(f"  - {tool}")
        print("\n💡 Install with: pip install -r requirements-dev.txt")
        return False

    print("✅ All code quality tools are installed")
    return True

def _is_tool_installed(tool_name):
    """Check if a tool is installed and available."""
    try:
        result = subprocess.run([tool_name, "--version"],
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def format_code():
    """Format code with Black and sort imports with isort."""
    print("🎨 Formatting code...")

    if not check_code_quality():
        print("❌ Cannot format - missing code quality tools")
        return False

    success = True

    # Format with Black
    try:
        result = subprocess.run(["black", "."], check=True, capture_output=True, text=True)
        print("✅ Black formatting completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Black formatting failed: {e}")
        success = False

    # Sort imports with isort
    try:
        result = subprocess.run(["isort", "."], check=True, capture_output=True, text=True)
        print("✅ Import sorting completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Import sorting failed: {e}")
        success = False

    return success

def lint_code():
    """Lint code with flake8 and mypy."""
    print("🔍 Linting code...")

    if not check_code_quality():
        print("❌ Cannot lint - missing code quality tools")
        return False

    success = True

    # Lint with flake8
    try:
        result = subprocess.run(["flake8", "."], check=True, capture_output=True, text=True)
        print("✅ Flake8 linting completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Flake8 linting failed: {e}")
        success = False

    # Type check with mypy (optional)
    try:
        result = subprocess.run(["mypy", "src/", "config/", "gui/", "tools/"], check=False, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MyPy type checking completed")
        else:
            print("⚠️ MyPy found type issues (this is optional)")
            print(result.stdout)
    except Exception as e:
        print(f"⚠️ MyPy type checking failed: {e}")

    return success

def clean_imports():
    """Remove unused imports and clean code."""
    print("🧹 Cleaning imports...")

    # First format and sort imports
    if not format_code():
        print("❌ Import cleaning failed during formatting")
        return False

    # Run autoflake to remove unused imports (optional)
    try:
        if _is_tool_installed("autoflake"):
            result = subprocess.run([
                "autoflake", "--in-place", "--remove-unused-variables",
                "--remove-all-unused-imports", "--recursive", "."
            ], check=True, capture_output=True, text=True)
            print("✅ Unused imports removed")
        else:
            print("⚠️ autoflake not installed - skipping unused import removal")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ autoflake failed: {e}")

    return True

def run_all_quality_checks():
    """Run all code quality checks."""
    print("🔍 Running complete code quality check...")

    success = True

    if not check_code_quality():
        print("❌ Cannot run quality checks - missing tools")
        return False

    if not format_code():
        success = False

    if not lint_code():
        success = False

    if success:
        print("✅ All code quality checks passed!")
    else:
        print("❌ Some code quality checks failed")

    return success
