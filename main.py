#!/usr/bin/env python3
"""
EPSON PP-100 Disc Burner Application Launcher

This script serves as the main entry point for the application,
importing the actual implementation from the src/ directory.
"""

import sys
import os

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

# Import and run the main application
from main import main

if __name__ == "__main__":
    sys.exit(main())
