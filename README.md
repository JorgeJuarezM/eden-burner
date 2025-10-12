# EPSON PP-100 Disc Burner Application

Aplicación profesional para gestión de quemado de discos con robot EPSON PP-100.

## 🏗️ Estructura del Proyecto

```
epson-burner-app/
├── src/                          # Código fuente principal
│   ├── main.py                   # Punto de entrada de la aplicación
│   ├── background_worker.py      # Trabajador en segundo plano
│   ├── job_queue.py              # Gestión de cola de trabajos
│   ├── iso_downloader.py         # Descarga de archivos ISO
│   ├── jdf_generator.py          # Generación de archivos JDF
│   ├── graphql_client.py         # Cliente GraphQL API
│   └── local_storage.py          # Gestión de almacenamiento local
├── config/                       # Configuración de la aplicación
│   ├── config.py                 # Gestor de configuración
│   ├── config.yaml              # Configuración del usuario
│   └── config.example.yaml      # Ejemplo de configuración
├── gui/                         # Interfaz gráfica de usuario
│   ├── main_window.py           # Ventana principal
│   └── __init__.py
├── docs/                        # Documentación
│   ├── README.md               # Este archivo
│   ├── BUILD_README.md        # Guía de construcción
│   ├── DEVELOPMENT_README.md   # Guía de desarrollo
│   ├── DISTRIBUTION_README.md  # Guía de distribución
│   └── LICENSE.txt             # Licencia
├── tools/                       # Herramientas de desarrollo
│   ├── dev_tools.py            # Herramientas de desarrollo
│   ├── test_config.py          # Pruebas de configuración
│   └── __init__.py
├── scripts/                     # Scripts de construcción y despliegue
│   ├── build.py                # Script de construcción principal
│   ├── create_windows_package.py # Empaquetado para Windows
│   ├── rebuild.py              # Reconstrucción completa
│   └── __init__.py
├── main.py                      # Launcher principal (raíz)
├── requirements.txt             # Dependencias Python
├── requirements-dev.txt         # Dependencias de desarrollo
└── README.md                    # Archivo README principal
```

## 🚀 Inicio Rápido

### Instalación

1. **Crear entorno virtual:**
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar aplicación:**
```bash
cp config/config.example.yaml config/config.yaml
# Editar config/config.yaml con tus valores
```

### Ejecución

```bash
# Ejecutar aplicación completa (GUI)
python3 main.py

# Ejecutar en modo background (solo bandeja del sistema)
python3 main.py --background

# Probar configuración
python3 main.py --test-config
```

## 📋 Características Principales

- **🔍 Consulta GraphQL**: Descubrimiento automático de ISOs vía API
- **📋 Gestión de trabajos**: Cola de trabajos con prioridades
- **🔄 Procesamiento automático**: Descarga, generación JDF y quemado
- **🎨 Interfaz moderna**: GUI responsiva con información DICOM
- **⚙️ Configuración flexible**: Archivo YAML personalizable
- **🗄️ Persistencia**: Base de datos SQLite con respaldo automático

## 🔧 Configuración

Editar `config/config.yaml`:

```yaml
api:
  graphql_endpoint: "https://tu-api.com/graphql"
  api_key: "tu-clave-api"
  timeout: 30

robot:
  robot_uuid: "uuid-unico-del-robot"
  burn_speed: "8x"
  verify_after_burn: true

jobs:
  max_concurrent: 3
  check_interval: 30
```

## 📚 Documentación Adicional

- [Guía de Desarrollo](docs/DEVELOPMENT_README.md)
- [Guía de Construcción](docs/BUILD_README.md)
- [Guía de Distribución](docs/DISTRIBUTION_README.md)

## 🛠️ Desarrollo

Para desarrollo:

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar pruebas
python3 tools/test_config.py

# Herramientas de desarrollo
python3 tools/dev_tools.py
```

## 📦 Construcción y Despliegue

```bash
# Construir aplicación
python3 scripts/build.py

# Crear paquete para Windows
python3 scripts/create_windows_package.py

# Reconstruir completamente
python3 scripts/rebuild.py
```

## 📄 Licencia

Ver [LICENSE.txt](docs/LICENSE.txt) para detalles de la licencia.
