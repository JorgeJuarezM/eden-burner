#!/usr/bin/env python3
"""
Simple build script for EPSON PP-100 Disc Burner Application
"""

import os
import platform
import subprocess
import sys


def get_venv_python():
    """Get the Python executable from the virtual environment."""
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python3")
    if os.path.exists(venv_python):
        return venv_python
    else:
        # Fallback to current Python
        return sys.executable


def build_simple():
    """Build a simple executable using PyInstaller defaults."""
    print("Building executable...")

    python_exe = get_venv_python()
    print(f"Using Python: {python_exe}")

    current_platform = platform.system().lower()
    is_windows = current_platform == "windows"
    is_darwin = current_platform == "darwin"
    is_linux = current_platform == "linux"

    if is_darwin:
        icon_path = "icon.icns"
    elif is_windows:
        icon_path = "icon.ico"
    elif is_linux:
        icon_path = "icon.png"
    else:
        raise ValueError(f"Unsupported platform: {current_platform}")

    # Simple PyInstaller command
    cmd = [
        python_exe,
        "-m",
        "PyInstaller",
        "--onefile" if is_windows else "--onedir",
        "--windowed" if is_windows else "--noconsole",
        "--name=Eden Burner",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=PyQt5.QtNetwork",
        "--hidden-import=PyQt5.QtPrintSupport",
        "--hidden-import=schedule",
        "--hidden-import=yaml",
        "--hidden-import=sqlalchemy.ext.baked",
        "--noconfirm",
        f"--icon=assets/{icon_path}",
        "main.py",
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("✓ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False


if __name__ == "__main__":
    success = build_simple()
    if success:
        print("\n🎉 Executable created in 'dist/' directory!")
        print("📁 Check 'dist/Eden Burner' for the executable")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)
