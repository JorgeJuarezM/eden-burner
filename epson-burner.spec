# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import platform

def get_main_script():
    """Get the main script path relative to the spec file."""
    return os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'main.py')

def get_resources():
    """Get resources directory."""
    return os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'resources')

def get_templates():
    """Get templates directory."""
    return os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'templates')

def get_gui_files():
    """Get GUI directory files."""
    gui_dir = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'gui')
    if os.path.exists(gui_dir):
        gui_files = []
        for root, dirs, files in os.walk(gui_dir):
            for file in files:
                gui_files.append((os.path.join(root, file), os.path.join('gui', os.path.relpath(root, gui_dir), file)))
        return gui_files
    return []

block_cipher = None

# Platform-specific configuration
current_platform = platform.system().lower()
is_windows = current_platform == 'windows'
is_darwin = current_platform == 'darwin'
is_linux = current_platform == 'linux'

# Platform-specific binaries for macOS
macos_binaries = [
    ('/opt/homebrew/lib/libQt5Core.dylib', '.'),
    ('/opt/homebrew/lib/libQt5Widgets.dylib', '.'),
    ('/opt/homebrew/lib/libQt5Gui.dylib', '.'),
    ('/opt/homebrew/lib/libQt5Network.dylib', '.'),
    ('/opt/homebrew/lib/libQt5PrintSupport.dylib', '.'),
] if is_darwin else []

a = Analysis(
    [get_main_script()],
    pathex=[
        os.path.dirname(os.path.abspath(SPEC)),
    ],
    binaries=macos_binaries,
    datas=[
        # Include configuration files
        ('config.yaml', '.'),
        # Include GUI files
        *get_gui_files(),
        # Include templates if they exist
        (get_templates(), 'templates') if os.path.exists(get_templates()) else None,
        # Include resources if they exist
        (get_resources(), 'resources') if os.path.exists(get_resources()) else None,
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtNetwork',
        'PyQt5.QtPrintSupport',
        'PyQt5.sip',
        'sqlalchemy.ext.baked',
        'schedule',
        'yaml',
        'graphql_client',
        'iso_downloader',
        'jdf_generator',
        'local_storage',
        'background_worker',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'pytest',
        'nose',
        'coverage',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific executable configuration
exe_kwargs = {
    'name': 'epson-burner-app',
    'debug': False,
    'bootloader_ignore_signals': False,
    'strip': False,
    'upx': True,
    'upx_exclude': [],
    'runtime_tmpdir': None,
    'console': False,  # Hide console window
}

# Platform-specific icon
if is_windows and os.path.exists('resources/icon.ico'):
    exe_kwargs['icon'] = 'resources/icon.ico'
elif is_darwin and os.path.exists('resources/icon.icns'):
    exe_kwargs['icon'] = 'resources/icon.icns'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    **exe_kwargs
)

# macOS specific bundle configuration
if is_darwin:
    app = BUNDLE(
        exe,
        name='EPSON PP-100 Disc Burner',
        icon='resources/icon.icns' if os.path.exists('resources/icon.icns') else None,
        bundle_identifier='com.epson.discburner',
        info_plist={
            'CFBundleDisplayName': 'EPSON Disc Burner',
            'CFBundleName': 'EPSON Disc Burner',
            'CFBundleIdentifier': 'com.epson.discburner',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSBackgroundOnly': False,
        },
    )
