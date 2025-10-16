#!/usr/bin/env python3
"""
Simple build script for EPSON PP-100 Disc Burner Application

This script creates platform-specific executables using PyInstaller with optimized
settings for Windows, macOS, and Linux.

Requirements:
- PyInstaller (pip install PyInstaller)
- Python virtual environment (optional but recommended)

Usage:
    python scripts/build.py

The script will:
1. Detect the current platform (Windows, macOS, Linux)
2. Check for required dependencies
3. Use appropriate PyInstaller options for each platform
4. Create executable in the 'dist/' directory

Platform-specific behavior:
- Windows: Creates a single .exe file
- macOS: Creates a .app bundle (universal binary for Intel + Apple Silicon)
- Linux: Creates a directory with executable
"""


import os
import platform
import subprocess
import sys
from pathlib import Path


def get_icon_path():
    """Get the appropriate icon path for the current platform."""
    current_platform = platform.system().lower()
    script_dir = os.path.dirname(__file__)
    assets_dir = Path(script_dir).parent / "assets"

    # Define icon files for each platform
    icon_files = {
        "darwin": ["icon.icns", "icon.png"],
        "windows": ["icon.ico", "icon.png"],
        "linux": ["icon.png", "icon.ico"],
    }

    platform_icons = icon_files.get(current_platform, icon_files["linux"])

    # Check if assets directory exists
    if not os.path.exists(assets_dir):
        print(f"Warning: Assets directory not found at {assets_dir}")
        return None

    # Try each icon file for the platform
    for icon_file in platform_icons:
        icon_path = os.path.join(assets_dir, icon_file)
        if os.path.exists(icon_path):
            print(f"Icon found: {icon_path}")
            return Path("assets") / icon_file

    print(f"Warning: No suitable icon file found in {assets_dir}")
    print(f"Checked for: {', '.join(platform_icons)}")
    return None


def get_venv_python():
    """Get the Python executable from the virtual environment."""
    script_dir = os.path.dirname(__file__)
    current_platform = platform.system().lower()

    # Determine virtual environment paths based on platform
    if current_platform == "windows":
        venv_python = os.path.join(script_dir, "venv", "Scripts", "python.exe")
        # Also check for python3.exe
        if not os.path.exists(venv_python):
            venv_python = os.path.join(script_dir, "venv", "Scripts", "python3.exe")
    else:
        # Unix-like systems (Linux, macOS)
        venv_python = os.path.join(script_dir, "venv", "bin", "python3")
        # Also check for python
        if not os.path.exists(venv_python):
            venv_python = os.path.join(script_dir, "venv", "bin", "python")

    if os.path.exists(venv_python):
        return venv_python
    else:
        # Fallback to current Python
        print(f"Warning: Virtual environment Python not found at {venv_python}")
        print("Using system Python instead")
        return sys.executable


def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []

    # Check PyInstaller
    try:
        import PyInstaller  # noqa
        import PyQt5  # noqa
        import schedule  # noqa
        import sqlalchemy  # noqa
        import yaml  # noqa
    except ImportError:
        missing_deps.append("PyInstaller")

    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n💡 Install missing dependencies:")
        print(f"   pip install {' '.join(missing_deps)}")
        return False

    return True


def build_simple():
    """Build a simple executable using PyInstaller defaults."""
    print("Building executable...")

    # Check dependencies first
    if not check_dependencies():
        return False

    python_exe = get_venv_python()
    print(f"Using Python: {python_exe}")

    current_platform = platform.system().lower()
    is_windows = current_platform == "windows"
    is_darwin = current_platform == "darwin"
    is_linux = current_platform == "linux"

    if not (is_windows or is_darwin or is_linux):
        raise ValueError(f"Unsupported platform: {current_platform}")

    # Get icon path for this platform
    icon_path = get_icon_path()

    # Build PyInstaller command based on platform
    cmd = [python_exe, "-m", "PyInstaller", "--onedir"]

    # Output format options
    if is_windows:
        cmd.extend(["--windowed"])
    else:
        cmd.extend(["--noconsole"])

    # Application name
    cmd.extend(["--name=Eden Burner"])

    # Hidden imports for common dependencies
    hidden_imports = [
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.QtNetwork",
        "PyQt5.QtPrintSupport",
        "schedule",
        "yaml",
        "sqlalchemy.ext.baked",
    ]

    for import_name in hidden_imports:
        cmd.extend([f"--hidden-import={import_name}"])

    # Icon (if available)
    if icon_path:
        cmd.extend([f"--icon={icon_path}"])
        print(f"Using icon: {icon_path}")
    else:
        print("No icon file found, building without icon")

    # Additional platform-specific options
    if is_darwin:
        cmd.extend(
            [
                "--osx-bundle-identifier=com.edenmed.epson-burner",
            ]
        )
        # macOS specific optimizations
        current_arch = platform.machine().lower()
        if current_arch == "arm64":
            cmd.extend(["--target-architecture=arm64"])
        else:
            cmd.extend(["--target-architecture=x86_64"])
    elif is_linux:
        # Linux specific options
        cmd.extend(
            [
                "--strip",  # Remove debug symbols
            ]
        )

    # Disable confirmation prompts
    cmd.extend(["--noconfirm"])

    # Main script
    cmd.append("main.py")

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
        current_platform = platform.system().lower()
        print("\n🎉 Executable created successfully!")

        if current_platform == "windows":
            print("📁 Check 'dist/Eden Burner.exe' for the executable")
        elif current_platform == "darwin":
            print("📁 Check 'dist/Eden Burner.app' for the application bundle")
        else:  # Linux and others
            print("📁 Check 'dist/Eden Burner/' directory for the executable")

        print("🚀 You can now distribute and run your application!")
    else:
        print("\n❌ Build failed!")
        print("💡 Check the error messages above for details")
        sys.exit(1)
