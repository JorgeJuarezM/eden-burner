#!/usr/bin/env python3
"""
Code Quality Tools for EPSON PP-100 Disc Burner Application

This script provides automated code formatting, linting, and import cleaning.
"""

import subprocess
import sys
from pathlib import Path

CODE_PATHS = ["app/", "config/", "gui/", "tools/", "scripts/"]


def run_command(cmd, description="", cwd=None):
    """Run a command and display output."""
    if cwd is None:
        cwd = Path(__file__).parent.parent

    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def check_tools():
    """Check if all required tools are installed."""
    print("🔍 Checking development tools...")

    required_tools = [
        ("black", "Black code formatter"),
        ("isort", "Import sorter"),
        ("flake8", "Python linter"),
        ("mypy", "Static type checker"),
    ]

    missing_tools = []
    for tool, description in required_tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            print(f"✅ {tool}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool}")
            missing_tools.append(f"{tool} ({description})")

    if missing_tools:
        print("❌ Missing tools:")
        for tool in missing_tools:
            print(f"  - {tool}")
        print("\n💡 Install with: pip install -r requirements-dev.txt")
        return False

    print("✅ All tools are installed")
    return True


def format_code():
    """Format code with Black and sort imports with isort."""
    print("🎨 Formatting code...")

    if not check_tools():
        print("❌ Cannot format - missing tools")
        return False

    success = True

    # Sort imports with isort
    if not run_command(["isort", "--profile", "black", *CODE_PATHS], "Import sorting"):
        success = False

    # Format with Black
    if not run_command(["black", *CODE_PATHS], "Black code formatting"):
        success = False

    return success


def lint_code():
    """Lint code with flake8 and mypy."""
    print("🔍 Linting code...")

    if not check_tools():
        print("❌ Cannot lint - missing tools")
        return False

    success = True

    # Lint with flake8
    if not run_command(["flake8", *CODE_PATHS], "Flake8 linting"):
        success = False

    # Type check with mypy (optional)
    try:
        run_command(["mypy", *CODE_PATHS], "MyPy type checking")
    except:
        print("⚠️  MyPy type checking had issues (this is optional)")

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
        if subprocess.run(["autoflake", "--version"], capture_output=True).returncode == 0:
            run_command(
                [
                    "autoflake",
                    "--in-place",
                    "--remove-unused-variables",
                    "--remove-all-unused-imports",
                    "--recursive",
                    *CODE_PATHS,
                ],
                "Autoflake unused import removal",
            )
        else:
            print("⚠️  autoflake not installed - skipping unused import removal")
    except:
        print("⚠️  autoflake had issues (this is optional)")

    return True


def run_quality_checks():
    """Run all code quality checks."""
    print("🔍 Running complete code quality check...")

    success = True

    if not check_tools():
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


def show_help():
    """Show available commands."""
    print("🚀 Code Quality Tools - Available Commands:")
    print()
    print("  format          - Format code with Black and sort imports")
    print("  lint            - Lint code with flake8 and mypy")
    print("  clean           - Remove unused imports and clean code")
    print("  quality         - Run all code quality checks")
    print("  check-tools     - Check if all tools are installed")
    print("  help            - Show this help message")
    print()
    print("Examples:")
    print("  python3 scripts/code_quality.py format")
    print("  python3 scripts/code_quality.py quality")
    print("  python3 scripts/code_quality.py clean")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        return 1

    command = sys.argv[1]

    commands = {
        "format": format_code,
        "lint": lint_code,
        "clean": clean_imports,
        "quality": run_quality_checks,
        "check-tools": check_tools,
        "help": show_help,
    }

    if command not in commands:
        print(f"❌ Unknown command: {command}")
        show_help()
        return 1

    success = commands[command]()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
