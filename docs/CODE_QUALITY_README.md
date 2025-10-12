# 🛠️ Herramientas de Desarrollo - Guía de Uso

## 📋 Descripción

Este proyecto incluye herramientas automatizadas para mantener la calidad del código, formateo consistente y limpieza de imports no utilizados.

## 🛠️ Instalación de Herramientas

```bash
# Instalar herramientas de desarrollo
pip install -r requirements-dev.txt

# Las herramientas incluyen:
# - black: Formateador de código
# - isort: Ordenador de imports
# - flake8: Linter de Python
# - mypy: Verificador de tipos
# - autoflake: Removedor de imports no utilizados
```

## 🚀 Comandos Disponibles

### Formateo de Código

```bash
# Formatear todo el código con Black
python3 scripts/code_quality.py format

# Solo ordenar imports con isort
python3 tools/dev_tools.py --format-code
```

### Análisis de Código

```bash
# Ejecutar análisis completo de calidad
python3 scripts/code_quality.py quality

# Solo linting con flake8 y mypy
python3 scripts/code_quality.py lint

# Verificar que todas las herramientas estén instaladas
python3 scripts/code_quality.py check-tools
```

### Limpieza de Código

```bash
# Limpiar imports no utilizados y formatear
python3 scripts/code_quality.py clean

# Solo limpiar imports (más agresivo)
python3 tools/dev_tools.py --clean-imports
```

## 📋 Ejemplos de Uso

### Flujo de Trabajo Recomendado

```bash
# 1. Verificar herramientas
python3 scripts/code_quality.py check-tools

# 2. Formatear código
python3 scripts/code_quality.py format

# 3. Ejecutar análisis completo
python3 scripts/code_quality.py quality

# 4. Limpiar imports no utilizados (opcional)
python3 scripts/code_quality.py clean
```

### Comandos Específicos

```bash
# Formatear solo archivos específicos
black src/ config/

# Ordenar imports en un directorio específico
isort src/

# Ejecutar linter en archivos específicos
flake8 src/main.py config/config.py

# Verificar tipos solo en módulos principales
mypy src/ config/
```

## ⚙️ Configuración

### Black (Formateo)
- **Longitud de línea**: 100 caracteres
- **Versión objetivo**: Python 3.8+
- **Exclusiones**: directorios virtuales, build, dist

### isort (Orden de Imports)
- **Perfil**: black (compatible con Black)
- **Longitud de línea**: 100 caracteres
- **Agrupación**: STDLIB → THIRDPARTY → FIRSTPARTY → LOCALFOLDER

### flake8 (Linting)
- **Estándar**: PEP 8
- **Exclusiones**: __pycache__, .venv, build, dist

## 🔧 Consejos para Desarrollo

### Antes de Hacer Commit
```bash
# Siempre ejecutar antes de commit
python3 scripts/code_quality.py quality
```

### Durante Desarrollo Activo
```bash
# Formatear frecuentemente durante desarrollo
python3 scripts/code_quality.py format

# Ejecutar análisis rápido
python3 scripts/code_quality.py lint
```

### Para Código Problemático
```bash
# Si hay conflictos de formato
python3 scripts/code_quality.py clean

# Verificar tipos específicos
mypy src/specific_file.py
```

## 📊 Salida Esperada

### Formateo Exitoso
```
============================================================
Running: Black code formatting
Command: black .
============================================================
✅ Black code formatting completed successfully
```

### Análisis Limpio
```
============================================================
Running: Flake8 linting
Command: flake8 .
============================================================
✅ Flake8 linting completed successfully
```

### Errores Encontrados
```
============================================================
Running: Flake8 linting
Command: flake8 .
============================================================
❌ Flake8 linting failed
Exit code: 1
./src/main.py:45:1: E302 expected 2 blank lines, found 1
```

## 🎯 Beneficios

✅ **Código consistente** - Formato uniforme en todo el proyecto
✅ **Imports organizados** - Orden lógico y eliminación automática
✅ **Errores tempranos** - Detección de problemas antes de ejecución
✅ **Mantenimiento fácil** - Código limpio y legible
✅ **Estándares profesionales** - Cumple con mejores prácticas de Python

## 🚨 Solución de Problemas

### Error: "command not found"
```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar herramientas faltantes
pip install -r requirements-dev.txt
```

### Error: "Import not found"
```bash
# Verificar que estás en el directorio correcto
pwd  # Debería mostrar la raíz del proyecto

# Ejecutar desde la raíz del proyecto
python3 scripts/code_quality.py format
```

### Error: "Permission denied"
```bash
# Hacer el script ejecutable
chmod +x scripts/code_quality.py
```

## 📚 Recursos Adicionales

- [Black Documentation](https://black.readthedocs.io/)
- [isort Documentation](https://pycqa.github.io/isort/)
- [flake8 Documentation](https://flake8.pycqa.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
