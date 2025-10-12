#!/usr/bin/env python3
"""
Build script for EPSON PP-100 Disc Burner Application
Creates executable packages for Windows, macOS, and Linux using PyInstaller.
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path


def install_dependencies():
    """Install development dependencies."""
    print("Installing development dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'
        ])
        print("✓ Development dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install development dependencies: {e}")
        return False
    return True


def clean_build():
    """Clean previous build artifacts."""
    print("Cleaning previous build artifacts...")

    # Remove common build directories
    build_dirs = ['build', 'dist', '__pycache__', '*.pyc', '*.spec~']
    for item in build_dirs:
        if item.endswith('/'):
            if os.path.exists(item):
                shutil.rmtree(item)
                print(f"  Removed: {item}")
        else:
            # Remove files matching pattern
            for file in Path('.').glob(item):
                if file.is_file():
                    file.unlink()
                    print(f"  Removed: {file}")

    print("✓ Build artifacts cleaned")


def build_executable(platform=None, onefile=True, clean=True):
    """Build executable for the specified platform."""
    if clean:
        clean_build()

    if not install_dependencies():
        return False

    print(f"Building executable for {platform or 'current platform'}...")

    # Use the spec file directly - PyInstaller will use the configuration from the spec file
    cmd = [sys.executable, '-m', 'PyInstaller', 'epson-burner.spec']

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✓ Build completed successfully for {platform or 'current platform'}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False


def build_all_platforms():
    """Build executables for all supported platforms."""
    print("Building executables for all platforms...")

    platforms = [
        ('windows', 'Windows'),
        ('macos', 'macOS'),
        ('linux', 'Linux')
    ]

    results = {}
    for platform_name, platform_display in platforms:
        print(f"\n{'='*50}")
        print(f"Building for {platform_display}...")
        print(f"{'='*50}")

        success = build_executable(platform_name, clean=False)  # Don't clean between builds
        results[platform_name] = success

        if success:
            print(f"✓ {platform_display} build completed")
        else:
            print(f"✗ {platform_display} build failed")

    print(f"\n{'='*50}")
    print("BUILD SUMMARY")
    print(f"{'='*50}")
    for platform, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{platform.upper()}: {status}")

    return all(results.values())


def main():
    parser = argparse.ArgumentParser(description='Build EPSON Disc Burner executables')
    parser.add_argument('--platform', choices=['windows', 'macos', 'linux', 'all'],
                       default='all', help='Target platform (default: all)')
    parser.add_argument('--onefile', action='store_true', default=True,
                       help='Create single file executable (default: True)')
    parser.add_argument('--no-clean', action='store_true',
                       help='Skip cleaning build artifacts')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode for PyInstaller')

    args = parser.parse_args()

    print("EPSON PP-100 Disc Burner - Build Script")
    print("="*50)

    # Add debug flag to PyInstaller if requested
    if args.debug:
        os.environ['PYINSTALLER_DEBUG'] = '1'

    if args.platform == 'all':
        success = build_all_platforms()
    else:
        success = build_executable(args.platform, onefile=args.onefile, clean=not args.no_clean)

    if success:
        print("\n🎉 Build process completed successfully!")
        print("\nExecutables can be found in the 'dist/' directory:")
        if os.path.exists('dist'):
            for item in os.listdir('dist'):
                item_path = os.path.join('dist', item)
                if os.path.isfile(item_path) or os.path.isdir(item_path):
                    print(f"  - {item}")
        else:
            print("  No dist directory found")
    else:
        print("\n❌ Build process failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
