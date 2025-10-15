import os
import platform
import subprocess
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# # Add the scripts directory to the path to import build
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from scripts.build import get_venv_python, get_icon_path, check_dependencies


class TestBuildScript:
    """Test suite for build.py functions using pytest."""

    @pytest.fixture
    def temp_dir(self):
        """Fixture to create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmp:
            yield tmp

    @pytest.mark.parametrize("platform_name,expected_path", [
        ("windows", "venv/Scripts/python.exe"),
        ("linux", "venv/bin/python3"),
        ("darwin", "venv/bin/python3"),
    ])
    @patch('os.path.exists')
    def test_get_venv_python_platform_specific(self, mock_exists, platform_name, expected_path):
        """Test get_venv_python for different platforms."""
        mock_exists.return_value = True
        with patch('platform.system', return_value=platform_name):
            result = get_venv_python()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            expected = os.path.join(current_dir, '../scripts', expected_path)
            expected = Path(expected).resolve().__str__()
            assert result == expected

    @patch('platform.system')
    @patch('os.path.exists')
    def test_get_venv_python_fallback(self, mock_exists, mock_system):
        """Test get_venv_python fallback when venv doesn't exist."""
        mock_system.return_value = 'Linux'
        mock_exists.return_value = False
        with patch('sys.executable', '/usr/bin/python3'):
            result = get_venv_python()
            assert result == '/usr/bin/python3'

    @pytest.mark.parametrize("platform_name,icon_files", [
        ("darwin", ["icon.icns"]),
    ])
    @patch('os.path.exists')
    def test_get_icon_path_success(self, mock_exists, platform_name, icon_files):
        """Test get_icon_path when icon is found."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(current_dir, '../assets')
        assets_dir = Path(assets_dir).resolve().__str__()
        icon_path = os.path.join(assets_dir, icon_files[0])

        def exists_side_effect(path):
            return path == assets_dir or path == icon_path

        mock_exists.side_effect = exists_side_effect
        with patch('platform.system', return_value=platform_name):
            result = get_icon_path()
            assert result == icon_path

    @patch('platform.system')
    @patch('os.path.exists')
    def test_get_icon_path_no_assets_dir(self, mock_exists, mock_system):
        """Test get_icon_path when assets directory doesn't exist."""
        mock_system.return_value = 'Linux'
        mock_exists.return_value = False
        result = get_icon_path()
        assert result is None

    def test_check_dependencies_missing_pyinstaller(self):
        """Test check_dependencies when PyInstaller is missing."""
        with patch.dict('sys.modules', {'PyInstaller': None}):
            result = check_dependencies()
            assert result is False

    def test_check_dependencies_all_present(self):
        """Test check_dependencies when all dependencies are present."""
        # Mock imports to succeed

        def mock_import(name, *args, **kwargs):
            if name in ['PyInstaller', 'PyQt5', 'schedule', 'sqlalchemy', 'yaml']:
                return MagicMock()
            return __import__(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            result = check_dependencies()
            assert result is True

    @patch('subprocess.run')
    @patch('platform.system')
    def test_build_simple_success(self, mock_system, mock_subprocess):
        """Test build_simple with successful build."""
        mock_system.return_value = 'Linux'
        mock_subprocess.return_value = MagicMock()

        with patch('scripts.build.get_venv_python', return_value='/fake/python'), \
             patch('scripts.build.get_icon_path', return_value='/fake/icon.png'), \
             patch('scripts.build.check_dependencies', return_value=True):

            from scripts.build import build_simple
            result = build_simple()
            assert result is True
            mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    @patch('platform.system')
    def test_build_simple_failure(self, mock_system, mock_subprocess):
        """Test build_simple with failed build."""
        mock_system.return_value = 'Linux'
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'pyinstaller')

        with patch('scripts.build.get_venv_python', return_value='/fake/python'), \
             patch('scripts.build.get_icon_path', return_value='/fake/icon.png'), \
             patch('scripts.build.check_dependencies', return_value=True):

            from scripts.build import build_simple
            result = build_simple()
            assert result is False


if __name__ == '__main__':
    pytest.main([__file__])
