# 🔧 Guía de Desarrollo - EPSON PP-100 Disc Burner

Esta guía proporciona herramientas y configuraciones para desarrollar y hacer debugging de la aplicación.

## 🚀 Inicio Rápido

### 1. Configuración del Entorno

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno
source venv/bin/activate  # Linux/macOS
# o
venv\\Scripts\\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Instalar herramientas de desarrollo adicionales
pip install black flake8 pytest
```

### 2. Configuración VS Code

1. **Abrir proyecto** en VS Code
2. **Instalar extensión Python** (ms-python.python)
3. **Seleccionar intérprete**: `./venv/bin/python3`
4. **Configuraciones disponibles** en `.vscode/launch.json`

## 🐛 Debugging

### Configuraciones de Debug Disponibles

| Configuración | Descripción | Uso |
|---------------|-------------|-----|
| **Python: Current File** | Ejecuta el archivo actual | F5 en cualquier `.py` |
| **Python: Main Application** | Ejecuta `main.py --background` | Debug del proceso principal |
| **Python: Main Application (GUI)** | Ejecuta `main.py` con interfaz | Debug con ventana visible |
| **Python: Build Script** | Ejecuta `build_simple.py` | Debug del proceso de construcción |
| **Python: Test Configuration** | Prueba carga de configuración | Debug de configuración |

### Atajos de Debug

- **F5**: Iniciar debugging
- **Ctrl+Shift+D**: Panel de debug
- **F10**: Step over
- **F11**: Step into
- **Shift+F11**: Step out
- **Ctrl+Shift+F5**: Reiniciar

## 🛠️ Herramientas de Desarrollo

### Script de Desarrollo (`dev_tools.py`)

```bash
# Ejecutar aplicación con debugging
python dev_tools.py --run

# Probar configuración
python dev_tools.py --test-config

# Verificar dependencias
python dev_tools.py --check-deps

# Ejecutar tests
python dev_tools.py --test

# Crear configuración de desarrollo
python dev_tools.py --create-dev-config
```

### Configuración de Desarrollo

Crear `config.dev.yaml` para desarrollo:

```bash
python dev_tools.py --create-dev-config
```

Esta configuración incluye:
- ✅ Debug detallado habilitado
- ✅ Logging nivel DEBUG
- ✅ Verificación deshabilitada para desarrollo rápido
- ✅ Configuración específica para desarrollo

## 📝 Configuración IDE

### VS Code Settings

El archivo `.vscode/settings.json` incluye:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python3",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### Características Automáticas

- 🔧 **Formateo automático** con Black al guardar
- 📦 **Ordenamiento de imports** automático
- 🔍 **Linter activado** (flake8)
- 🧪 **Soporte para pytest**
- 🐍 **Activación automática de entorno virtual**

## 🔧 Variables de Entorno

### Variables Disponibles

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `EPSON_DEBUG` | Habilitar modo debug detallado | `0` |
| `PYTHONPATH` | Path de Python para imports | `${workspaceFolder}` |
| `DISPLAY` | Display para aplicaciones GUI | `${env:DISPLAY}` |

### Uso en Debug

Las configuraciones de launch incluyen estas variables automáticamente.

## 📊 Logging y Debug

### Niveles de Log

- **DEBUG**: Información detallada para desarrollo
- **INFO**: Información general (por defecto)
- **WARNING**: Advertencias importantes
- **ERROR**: Errores que requieren atención

### Habilitar Debug

```python
import logging

# En tu código
logging.getLogger().setLevel(logging.DEBUG)

# O usar configuración
development:
  debug_mode: true
  log_level: "DEBUG"
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Usando dev_tools
python dev_tools.py --test

# Directamente con pytest
pytest . -v

# Tests específicos
pytest tests/test_config.py -v
```

### Cobertura de Tests

```bash
# Instalar cobertura
pip install pytest-cov

# Ejecutar con cobertura
pytest --cov=. --cov-report=html
```

## 🚀 Flujo de Trabajo de Desarrollo

### 1. Desarrollo con Debug

```bash
# 1. Iniciar aplicación en modo debug
python dev_tools.py --run

# 2. Usar VS Code debugger para breakpoints
# 3. Ver logs detallados en consola
```

### 2. Testing

```bash
# 1. Ejecutar tests automáticamente
python dev_tools.py --test

# 2. Verificar configuración
python dev_tools.py --test-config
```

### 3. Construcción y Distribución

```bash
# 1. Construir ejecutable
python build_simple.py

# 2. Crear instalador (si es necesario)
python create_windows_package.py
```

## 📋 Consejos de Desarrollo

### Breakpoints Útiles

1. **Inicio de aplicación** (`main.py`)
2. **Carga de configuración** (`config.py`)
3. **Inicialización de GUI** (`gui/main_window.py`)
4. **Procesamiento de trabajos** (`background_worker.py`)
5. **Comunicación API** (`graphql_client.py`)

### Debugging de GUI

Para debugging de interfaz gráfica:
1. Usar configuración **"Python: Main Application (GUI)"**
2. Establecer breakpoints en eventos de UI
3. Inspeccionar estado de widgets en tiempo real

### Performance Profiling

```python
import cProfile

# Para profiling de rendimiento
cProfile.run('main()', sort='cumulative')
```

## 🔒 Configuración de Seguridad

- ✅ `config.yaml` ignorado por git (contiene claves reales)
- ✅ `config.example.yaml` como plantilla pública
- ✅ Configuración por defecto segura
- ✅ Variables sensibles en entorno local

## 📞 Soporte

Para problemas de desarrollo:
1. Revisar logs con nivel DEBUG
2. Usar breakpoints en VS Code
3. Ejecutar tests automatizados
4. Verificar configuración con `dev_tools.py`

¡Feliz desarrollo! 🚀
