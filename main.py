#!/usr/bin/env python3
"""
EPSON PP-100 Disc Burner Application Launcher

This script serves as the main entry point for the application,
importing the actual implementation from the src/ directory.
"""

import sys

# Import and run the main application
from app.main import main

if __name__ == "__main__":
    sys.exit(main())
