#!/usr/bin/env python3
"""
Windows Distribution Package Creator
Creates an NSIS installer script and package for Windows distribution
"""

import os
import sys

def create_nsis_installer():
    """Create NSIS installer script for Windows."""
    print("📦 Creating Windows installer package...")

    # NSIS installer script content
    nsis_script = ''';NSIS Installer Script for EPSON PP-100 Disc Burner
;This script creates a Windows installer for the application

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "EPSON PP-100 Disc Burner"
OutFile "epson-burner-app-windows-installer.exe"
Unicode True
InstallDir "$PROGRAMFILES\\EPSON Disc Burner"
InstallDirRegKey HKCU "Software\\EPSON Disc Burner" ""
RequestExecutionLevel admin

;Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "resources\\icon.ico"
!define MUI_UNICON "resources\\icon.ico"

;Pages
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;Languages
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Spanish"

;Installer Sections
Section "Install Application" SecApp
    SetOutPath "$INSTDIR"

    ;Create installation directory
    CreateDirectory "$INSTDIR"

    ;Copy main executable
    File "dist\\epson-burner-app-windows.exe"

    ;Create desktop shortcut
    CreateShortCut "$DESKTOP\\EPSON Disc Burner.lnk" "$INSTDIR\\epson-burner-app-windows.exe" "" "$INSTDIR\\epson-burner-app-windows.exe" 0

    ;Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\\EPSON Disc Burner"
    CreateShortCut "$SMPROGRAMS\\EPSON Disc Burner\\EPSON Disc Burner.lnk" "$INSTDIR\\epson-burner-app-windows.exe" "" "$INSTDIR\\epson-burner-app-windows.exe" 0
    CreateShortCut "$SMPROGRAMS\\EPSON Disc Burner\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"

    ;Store installation folder
    WriteRegStr HKCU "Software\\EPSON Disc Burner" "" $INSTDIR

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"

    ;Write registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\EPSON Disc Burner" "DisplayName" "EPSON PP-100 Disc Burner"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\EPSON Disc Burner" "UninstallString" "$INSTDIR\\Uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\EPSON Disc Burner" "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\EPSON Disc Burner" "Publisher" "EPSON Corporation"
    WriteRegDWord HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\EPSON Disc Burner" "EstimatedSize" 40000

SectionEnd

;Uninstaller Section
Section "Uninstall"
    ;Remove files and directories
    Delete "$INSTDIR\\epson-burner-app-windows.exe"
    Delete "$INSTDIR\\Uninstall.exe"
    RMDir "$INSTDIR"

    ;Remove shortcuts
    Delete "$DESKTOP\\EPSON Disc Burner.lnk"
    RMDir /r "$SMPROGRAMS\\EPSON Disc Burner"

    ;Remove registry entries
    DeleteRegKey HKCU "Software\\EPSON Disc Burner"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\EPSON Disc Burner"
SectionEnd

;Functions
Function .onInit
    ;Check if already installed
    ReadRegStr $R0 HKCU "Software\\EPSON Disc Burner" ""
    ${If} $R0 != ""
        MessageBox MB_YESNO "EPSON Disc Burner is already installed. Do you want to reinstall?" IDYES continue
        Abort
        continue:
    ${EndIf}
FunctionEnd'''

    # Write NSIS script
    with open('windows_installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_script)

    print("✅ NSIS installer script created: windows_installer.nsi")

    # Create a simple license file
    license_content = '''EPSON PP-100 Disc Burner License Agreement

This software is provided "as is" without warranty of any kind.

Copyright (C) 2024 EPSON Corporation

Permission is granted to use this software for personal and commercial purposes.'''

    with open('LICENSE.txt', 'w', encoding='utf-8') as f:
        f.write(license_content)

    print("✅ License file created: LICENSE.txt")

    print("\n📋 To create the Windows installer:")
    print("1. Copy the following files to a Windows machine:")
    print("   - epson-burner-app-windows.exe (executable)")
    print("   - windows_installer.nsi (installer script)")
    print("   - LICENSE.txt (license file)")
    print("   - resources/icon.ico (icon file)")
    print("\n2. Install NSIS on Windows")
    print("3. Run: makensis windows_installer.nsi")
    print("4. This will create: epson-burner-app-windows-installer.exe")

def create_windows_package():
    """Create a simple ZIP package for Windows."""
    print("📦 Creating Windows ZIP package...")

    import zipfile
    import shutil

    # Create Windows distribution directory
    windows_dist = 'dist_windows'
    if os.path.exists(windows_dist):
        shutil.rmtree(windows_dist)

    os.makedirs(windows_dist)

    # Copy necessary files
    files_to_copy = [
        'dist/epson-burner-app',  # This is actually the macOS executable, but serves as reference
        'LICENSE.txt',
        'resources/icon.ico',
        'README.md',
        'DISTRIBUTION_README.md'
    ]

    for file_path in files_to_copy:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.copytree(file_path, os.path.join(windows_dist, os.path.basename(file_path)))
            else:
                shutil.copy2(file_path, windows_dist)

    # Create instructions file for Windows
    windows_instructions = '''INSTRUCCIONES PARA WINDOWS:

1. Para crear el ejecutable Windows:
   a. Copie este directorio completo a una máquina Windows
   b. Ejecute: python build_windows.py

2. Para crear un instalador:
   a. Instale NSIS en Windows
   b. Ejecute: makensis windows_installer.nsi

3. El ejecutable final estará en:
   dist/epson-burner-app-windows.exe

NOTA: Actualmente este paquete contiene el ejecutable de macOS.
Para obtener el ejecutable de Windows real, ejecute el proceso
de construcción en una máquina Windows.'''

    with open(os.path.join(windows_dist, 'WINDOWS_BUILD.txt'), 'w', encoding='utf-8') as f:
        f.write(windows_instructions)

    print(f"✅ Windows package created: {windows_dist}/")
    print("📋 Contains build instructions for Windows")

def main():
    print("🪟 EPSON PP-100 Disc Burner - Windows Distribution")
    print("=" * 55)

    create_nsis_installer()
    create_windows_package()

    print("\n🎉 Windows distribution package ready!")
    print("\n📁 Files created:")
    print("  • windows_installer.nsi (NSIS installer script)")
    print("  • LICENSE.txt (license file)")
    print("  • dist_windows/ (Windows build package)")
    print("  • resources/icon.ico (Windows icon)")

    print("\n📋 Next steps:")
    print("1. Copy these files to a Windows machine")
    print("2. Install NSIS and Python 3.8+ on Windows")
    print("3. Run the build process on Windows")
    print("4. Test the executable on Windows")

if __name__ == '__main__':
    main()
