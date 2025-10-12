;NSIS Installer Script for EPSON PP-100 Disc Burner
;This script creates a Windows installer for the application

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "EPSON PP-100 Disc Burner"
OutFile "epson-burner-app-windows-installer.exe"
Unicode True
InstallDir "$PROGRAMFILES\EPSON Disc Burner"
InstallDirRegKey HKCU "Software\EPSON Disc Burner" ""
RequestExecutionLevel admin

;Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "resources\icon.ico"
!define MUI_UNICON "resources\icon.ico"

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
    File "dist\epson-burner-app-windows.exe"

    ;Create desktop shortcut
    CreateShortCut "$DESKTOP\EPSON Disc Burner.lnk" "$INSTDIR\epson-burner-app-windows.exe" "" "$INSTDIR\epson-burner-app-windows.exe" 0

    ;Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\EPSON Disc Burner"
    CreateShortCut "$SMPROGRAMS\EPSON Disc Burner\EPSON Disc Burner.lnk" "$INSTDIR\epson-burner-app-windows.exe" "" "$INSTDIR\epson-burner-app-windows.exe" 0
    CreateShortCut "$SMPROGRAMS\EPSON Disc Burner\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

    ;Store installation folder
    WriteRegStr HKCU "Software\EPSON Disc Burner" "" $INSTDIR

    ;Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ;Write registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EPSON Disc Burner" "DisplayName" "EPSON PP-100 Disc Burner"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EPSON Disc Burner" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EPSON Disc Burner" "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EPSON Disc Burner" "Publisher" "EPSON Corporation"
    WriteRegDWord HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EPSON Disc Burner" "EstimatedSize" 40000

SectionEnd

;Uninstaller Section
Section "Uninstall"
    ;Remove files and directories
    Delete "$INSTDIR\epson-burner-app-windows.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"

    ;Remove shortcuts
    Delete "$DESKTOP\EPSON Disc Burner.lnk"
    RMDir /r "$SMPROGRAMS\EPSON Disc Burner"

    ;Remove registry entries
    DeleteRegKey HKCU "Software\EPSON Disc Burner"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EPSON Disc Burner"
SectionEnd

;Functions
Function .onInit
    ;Check if already installed
    ReadRegStr $R0 HKCU "Software\EPSON Disc Burner" ""
    ${If} $R0 != ""
        MessageBox MB_YESNO "EPSON Disc Burner is already installed. Do you want to reinstall?" IDYES continue
        Abort
        continue:
    ${EndIf}
FunctionEnd