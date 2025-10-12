# EPSON PP-100 Disc Burner - Build and Distribution Guide

This guide explains how to build and distribute the EPSON PP-100 Disc Burner application as standalone executables for Windows, macOS, and Linux.

## Prerequisites

1. **Python 3.8+** with virtual environment
2. **PyQt5** and other dependencies (install with `pip install -r requirements.txt`)
3. **PyInstaller** (install with `pip install -r requirements-dev.txt`)

## Quick Start

### Build for Current Platform
```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Build executable
python build.py
```

### Build for Specific Platform
```bash
# Build for Windows
python build.py --platform windows

# Build for macOS
python build.py --platform macos

# Build for Linux
python build.py --platform linux

# Build for all platforms
python build.py --platform all
```

### Build Options
```bash
# Create single file executable (default)
python build.py --onefile

# Skip cleaning build artifacts
python build.py --no-clean

# Enable debug mode for troubleshooting
python build.py --debug
```

## Build Output

After successful build, executables will be created in the `dist/` directory:

- **Windows**: `dist/epson-burner-app-windows/`
- **macOS**: `dist/EPSON Disc Burner.app/`
- **Linux**: `dist/epson-burner-app-linux/`

## Comportamiento por Defecto

El ejecutable compilado tiene el siguiente comportamiento:

- **Por defecto**: Muestra la interfaz gráfica principal al iniciar
- **Modo background**: Usa `--background` para ejecutar solo con system tray (sin mostrar la ventana principal)

### Ejemplos de Uso

```bash
# Ejecutar con GUI (comportamiento por defecto)
./dist/epson-burner-app

# Ejecutar en modo background
./dist/epson-burner-app --background

# Ver todas las opciones
./dist/epson-burner-app --help
```

## Platform-Specific Notes

### Windows
- Requires Windows 7 or later
- Single `.exe` file created when using `--onefile`
- Console window hidden by default

### macOS
- Creates proper `.app` bundle
- Supports macOS 10.13 or later
- Application can be distributed via DMG or ZIP

### Linux
- Requires most Linux distributions with GUI support
- Single executable file created
- May require additional system libraries

## Troubleshooting

### Common Issues

1. **PyQt5 Import Errors**
   ```bash
   # Ensure PyQt5 is properly installed
   pip uninstall PyQt5 PyQt5-Qt5
   pip install PyQt5
   ```

2. **Missing Dependencies**
   ```bash
   # Install all dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Build Fails on Specific Platform**
   ```bash
   # Enable debug mode for detailed output
   python build.py --debug --platform [platform]
   ```

4. **Application Won't Start**
   ```bash
   # Check if all required files are included
   # Verify virtual environment is activated during build
   ```

### Debug Mode

Enable debug mode to get detailed information about the build process:

```bash
python build.py --debug
```

## Distribution

### Creating Release Packages

1. **ZIP Archive** (All platforms)
   ```bash
   cd dist
   zip -r epson-burner-app-[platform]-[version].zip epson-burner-app-[platform]/
   ```

2. **macOS DMG** (macOS only)
   ```bash
   # Install create-dmg (optional)
   brew install create-dmg

   # Create DMG
   create-dmg --volname "EPSON Disc Burner" --window-pos 200 120 --window-size 800 400 --icon-size 100 --app-drop-link 600 185 "EPSON Disc Burner.dmg" "dist/EPSON Disc Burner.app"
   ```

3. **Windows Installer** (Windows only)
   - Use NSIS or Inno Setup to create an installer
   - Include the executable and any required runtime libraries

## Development

### Adding New Dependencies

1. Add to `requirements.txt` for runtime dependencies
2. Add to `requirements-dev.txt` for build dependencies
3. Update `epson-burner.spec` if needed for hidden imports
4. Test build on all target platforms

### Custom Icons

Place icon files in the `resources/` directory:
- `icon.ico` - Windows icon (256x256 recommended)
- `icon.icns` - macOS icon set
- `icon.png` - Linux/application icon

## Version History

- **v1.0.0**: Initial release with PyInstaller support
- Cross-platform executable creation
- System tray integration
- Command line GUI option

## Support

For build issues or questions:
1. Check the troubleshooting section
2. Enable debug mode (`--debug`)
3. Review PyInstaller documentation
4. Check platform-specific requirements
