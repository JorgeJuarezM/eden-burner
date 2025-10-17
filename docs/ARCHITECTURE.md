# Arquitectura del Sistema - EPSON PP-100 Disc Burner

## Visión General

La aplicación EPSON PP-100 Disc Burner está diseñada con una arquitectura de 3 capas claramente definida que asegura mantenibilidad, escalabilidad y separación de responsabilidades.

```
┌──────────────────────────────────────────────────────────────────┐
│                        Presentation Layer (GUI)                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    PyQt5 Interface                          │ │
│  │  • MainWindow, JobTableWidget, SettingsDialog               │ │
│  │  • System tray integration                                  │ │
│  │  • Real-time job monitoring                                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│                     Business Logic Layer (App)                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Core Application                          │ │
│  │  • JobQueue, BackgroundWorker, MainApp                      │ │
│  │  • GraphQL API integration                                  │ │
│  │  • File management (ISO, JDF, templates)                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│                      Data Access Layer (DB)                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Database Services                         │ │
│  │  • SQLAlchemy ORM models                                    │ │
│  │  • Repository pattern implementation                        │ │
│  │  • Session management and transactions                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────────┤
│                   Configuration & Infrastructure                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 Configuration System                        │ │
│  │  • Singleton pattern implementation                         │ │
│  │  • YAML-based configuration                                 │ │
│  │  • Runtime validation and defaults                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Capas de la Arquitectura

### 1. Presentation Layer (Capa de Presentación)

**Tecnologías:** PyQt5, QML (potencial futuro)

**Componentes principales:**
- `gui/main_window.py` - Ventana principal con tabla de trabajos
- `gui/job_details_dialog.py` - Diálogo de detalles de trabajo
- `gui/job_table_widget.py` - Widget personalizado para tabla de trabajos
- `gui/settings_dialog.py` - Diálogo de configuración

**Responsabilidades:**
- ✅ Interfaz de usuario responsiva y moderna
- ✅ Actualización en tiempo real de estados de trabajo
- ✅ Gestión de configuración del usuario
- ✅ Notificaciones del sistema y bandeja del sistema
- ✅ Manejo de eventos de usuario

**Patrones utilizados:**
- Model-View-Controller (MVC) adaptado para PyQt5
- Observer pattern para actualizaciones de estado
- Lazy loading para componentes pesados

### 2. Business Logic Layer (Capa de Lógica de Negocio)

**Tecnologías:** Python 3.8+, threading, asyncio

**Componentes principales:**
- `app/main.py` - Coordinador principal de la aplicación
- `app/job_queue.py` - Gestión de cola de trabajos y procesamiento
- `app/background_worker.py` - Trabajador en segundo plano y programación
- `app/graphql_client.py` - Cliente para API GraphQL
- `app/iso_downloader.py` - Gestión de descargas de archivos ISO
- `app/jdf_generator.py` - Generación de archivos JDF para robot

**Responsabilidades:**
- ✅ Procesamiento de trabajos (descarga, generación JDF, quemado)
- ✅ Comunicación con API externa (GraphQL)
- ✅ Gestión de estado de trabajos y transiciones
- ✅ Coordinación entre componentes
- ✅ Manejo de errores y recuperación

**Patrones utilizados:**
- State Machine para transiciones de estado de trabajos
- Producer-Consumer para procesamiento de trabajos
- Strategy pattern para diferentes tipos de operaciones
- Command pattern para operaciones reversibles

### 3. Data Access Layer (Capa de Acceso a Datos)

**Tecnologías:** SQLAlchemy, SQLite

**Componentes principales:**
- `db/engine.py` - Gestión de conexiones y sesiones
- `db/models/` - Modelos ORM (BurnJobRecord, Base)
- `db/burn_job.py` - Servicios de acceso a datos

**Responsabilidades:**
- ✅ Persistencia de datos de trabajos
- ✅ Gestión de sesiones y transacciones
- ✅ Migraciones de base de datos
- ✅ Estadísticas y consultas complejas

**Patrones utilizados:**
- Repository pattern para abstracción de datos
- Unit of Work para gestión de transacciones
- Data Mapper para conversión objeto-relacional

### 4. Configuration & Infrastructure (Configuración e Infraestructura)

**Tecnologías:** YAML, Python dataclasses

**Componentes principales:**
- `config/config.py` - Sistema de configuración singleton

**Responsabilidades:**
- ✅ Gestión centralizada de configuración
- ✅ Validación de configuración
- ✅ Variables de entorno y archivos YAML
- ✅ Configuración en tiempo de ejecución

## Flujos de Datos Principales

### Flujo de Procesamiento de Trabajos

```
1. API Discovery    2. Job Creation    3. Download     4. JDF Gen     5. Burning
     ↓                   ↓              ↓              ↓              ↓
GraphQL API      →   JobQueue     →   ISO Downloader → JDF Gen    → Robot
     ↑                   ↑              ↑              ↑              ↑
     └─── Background Worker ←──────────┘              └─── File Management
```

### Flujo de Persistencia

```
Application Events → JobQueue → BurnJob → DB Service → SQLAlchemy → SQLite
                                ↑              ↓
                           Status Updates   ←  Query Results
```

### Flujo de Configuración

```
YAML File → Config Parser → Singleton Instance → Property Access → Components
```

## Modelo de Hilos (Threading Model)

### Modelo Principal

```
Main Thread (GUI)
    ├── UI Events & Updates
    ├── Job Queue Management
    └── Configuration Changes

Background Thread (Worker)
    ├── API Polling (schedule.every())
    ├── Job Processing Coordination
    └── Database Maintenance

Worker Threads (Per Job)
    ├── ISO Download (threading.Thread)
    ├── JDF Generation (threading.Thread)
    └── Burning Process (threading.Thread)
```

### Sincronización

- **RLock** para operaciones críticas en JobQueue
- **Queue** para comunicación entre threads
- **Event objects** para señales de estado
- **Callback pattern** para notificaciones asincrónicas

## Estrategia de Manejo de Errores

### Niveles de Error

1. **Errores de Red** (API, descarga) - Reintentos automáticos
2. **Errores de Archivo** (I/O, permisos) - Logging detallado
3. **Errores de Robot** (comunicación) - Estados de error específicos
4. **Errores de Base de Datos** - Transacciones rollback automáticas
5. **Errores de Configuración** - Validación estricta en inicio

### Estrategias de Recuperación

- **Retry automático** con backoff exponencial
- **Fallback a estados seguros** en errores críticos
- **Logging comprehensivo** para debugging
- **Notificaciones al usuario** para errores importantes

## Seguridad y Validación

### Validación de Datos

- **Esquema de configuración** con validación estricta
- **Sanitización de entradas** de API externa
- **Validación de tipos** en modelos de datos
- **Límites de tamaño** para archivos y operaciones

### Seguridad

- **Configuración segura** (no almacenamiento de credenciales)
- **Validación de rutas** para prevenir path traversal
- **Límites de recursos** para prevenir abuso
- **Logging seguro** (sin información sensible)

## Métricas y Monitoreo

### Métricas Principales

- **Tiempo de procesamiento** por trabajo
- **Tasa de éxito/fallo** de operaciones
- **Uso de recursos** (CPU, memoria, disco)
- **Tiempo de respuesta** de API externa
- **Estado del sistema** y componentes

### Monitoreo

- **Logs estructurados** con niveles apropiados
- **Métricas de rendimiento** en tiempo real
- **Alertas automáticas** para condiciones críticas
- **Dashboard de estado** accesible vía GUI

## Escalabilidad y Mantenimiento

### Diseño para Escalabilidad

- **Procesamiento asíncrono** para operaciones I/O intensivas
- **Configuración de concurrencia** ajustable
- **Separación de capas** para fácil extensión
- **Modularidad** para agregar nuevas funcionalidades

### Estrategias de Mantenimiento

- **Tests unitarios** para componentes críticos
- **Logging comprehensivo** para debugging
- **Configuración externa** para ajustes sin recompilación
- **Documentación actualizada** con cambios arquitectónicos

## Tecnologías y Dependencias

### Core Technologies

- **Python 3.8+** - Lenguaje principal
- **PyQt5** - Framework de interfaz gráfica
- **SQLAlchemy** - ORM y manejo de base de datos
- **aiohttp** - Cliente HTTP asíncrono
- **schedule** - Programación de tareas
- **PyYAML** - Parseo de configuración

### Dependencias de Desarrollo

- **pytest** - Framework de pruebas
- **black** - Formateo de código
- **flake8** - Linting de código
- **mypy** - Verificación de tipos
- **coverage** - Cobertura de pruebas

Este documento se mantiene actualizado con la evolución de la arquitectura y debe revisarse junto con cambios significativos en el código.
