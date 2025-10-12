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

        print("✅ Configuration loaded successfully"        print(f"📁 Downloads folder: {config.downloads_folder}")
        print(f"📁 JDF folder: {config.jdf_folder}")
        print(f"🔗 API endpoint: {config.graphql_endpoint}")
        print(f"🤖 Robot name: {config.robot_name}")

        # Validate configuration
        errors = config.validate_config()
        if errors:
            print("⚠️ Configuration warnings:"            for error in errors:
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
    parser.add_argument('--create-dev-config', action='store_true', help='Create development configuration')

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
    else:
        print("🔧 EPSON PP-100 Disc Burner - Development Tools")
        print("=" * 50)
        print("Available commands:")
        print("  --run                 Run application with debugging")
        print("  --test-config         Test configuration loading")
        print("  --check-deps          Check if all dependencies are installed")
        print("  --test                Run test suite")
        print("  --create-dev-config   Create development configuration file")
        print("\n💡 Use VS Code with .vscode/launch.json for full debugging support")

if __name__ == '__main__':
    main()
