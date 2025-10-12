#!/usr/bin/env python3
"""
Simple configuration test for EPSON PP-100 Disc Burner Application
Tests configuration without GUI dependencies
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import Config
except ImportError as e:
    print(f"Error importing config: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)

def test_config():
    """Test configuration loading and validation."""
    try:
        print("Testing configuration...")
        config = Config()

        # Test robot_uuid access
        print(f"Robot UUID: {config.robot_uuid}")
        print(f"Robot Name: {config.robot_name}")
        print(f"API Endpoint: {config.graphql_endpoint}")
        print(f"Max Concurrent Jobs: {config.max_concurrent_jobs}")

        # Test configuration validation
        errors = config.validate_config()
        if errors:
            print("Configuration errors found:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("Configuration is valid!")
            return True

    except Exception as e:
        print(f"Error testing configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
