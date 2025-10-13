#!/usr/bin/env python3
"""
Script de reconstrucción rápida para EPSON PP-100 Disc Burner
Reconstruye el ejecutable cuando hay cambios en el código fuente.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    print("🔄 Reconstruyendo aplicación EPSON PP-100 Disc Burner...")
    print("=" * 60)

    # Limpiar builds anteriores
    print("🧹 Limpiando builds anteriores...")
    build_dirs = ["build", "dist"]
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  ✓ Removido: {dir_name}/")

    # Ejecutar construcción
    print("\n🏗️  Construyendo ejecutable...")
    success = subprocess.call([sys.executable, "build_simple.py"])

    if success == 0:
        print("\n✅ Reconstrucción completada exitosamente!")
        print("\n📍 Ejecutable disponible en:")
        print("  • dist/epson-burner-app (ejecutable independiente)")
        print("  • dist/epson-burner-app.app (bundle macOS)")

        # Verificar tamaño del ejecutable
        exe_path = Path("dist/epson-burner-app")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n📊 Tamaño del ejecutable: {size_mb:.1f} MB")

    else:
        print("\n❌ Error durante la reconstrucción")
        sys.exit(1)


if __name__ == "__main__":
    main()
