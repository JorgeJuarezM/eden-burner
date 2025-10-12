#!/usr/bin/env python3
"""
Build script for Windows executable
Creates a standalone .exe file for Windows distribution
"""

import os
import sys
import subprocess

def build_windows_executable():
    """Build executable specifically for Windows."""
    print("🏗️ Building Windows executable...")

    # Use virtual environment Python
    python_exe = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python3')
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    print(f"Using Python: {python_exe}")

    # PyInstaller command for Windows executable
    cmd = [
        python_exe, '-m', 'PyInstaller',
        '--onefile',                    # Single executable file
        '--windowed',                   # No console window
        '--name=epson-burner-app-windows',  # Windows-specific name
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtNetwork',
        '--hidden-import=PyQt5.QtPrintSupport',
        '--hidden-import=schedule',
        '--hidden-import=yaml',
        '--hidden-import=sqlalchemy.ext.baked',
        '--icon=resources/icon.ico',     # Windows icon
        '--upx-dir=/usr/local/bin/',    # UPX location (if available)
        'main.py'
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("✅ Windows executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows build failed: {e}")
        return False

def main():
    print("🔨 EPSON PP-100 Disc Burner - Windows Build")
    print("=" * 50)

    success = build_windows_executable()

    if success:
        print("\n🎉 Windows executable created!")
        print("\n📁 Location: dist/epson-burner-app-windows.exe")
        print("📊 The executable is completely standalone and ready for Windows distribution")

        # Check file size
        exe_path = 'dist/epson-burner-app-windows.exe'
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📏 File size: {size_mb:.1f} MB")

    else:
        print("\n❌ Windows build failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
