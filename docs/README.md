# EPSON PP-100 Disc Burner Application

Una aplicación PyQt5 para gestionar trabajos de quemado de discos con el robot EPSON PP-100.

## Características

- **Consulta de ISOs vía GraphQL API**: Se conecta automáticamente a una API GraphQL para buscar nuevos archivos ISO
- **Gestión de cola de trabajos**: Soporta múltiples trabajos simultáneos con prioridades
- **Generación automática de archivos JDF**: Crea archivos JDF compatibles con el robot EPSON PP-100
- **Interfaz intuitiva**: GUI moderna con monitoreo en tiempo real de trabajos
- **Ejecución en segundo plano**: Continúa funcionando cuando se cierra la ventana principal
- **Sistema de notificaciones**: Notificaciones del sistema para trabajos completados o fallidos
- **Persistencia de datos**: Base de datos local para mantener el historial de trabajos

## Instalación

### Prerrequisitos

- Python 3.8 o superior
- PyQt5
- SQLAlchemy
- requests
- gql (para GraphQL)
- aiohttp
- pyyaml

### Instalación con pip

```bash
cd /Users/jorgejuarez/CascadeProjects/epson-burner-app
pip install -r requirements.txt
```

### Instalación en macOS

```bash
# Instalar PyQt5
pip install PyQt5

# Instalar otras dependencias
pip install sqlalchemy requests gql[aiohttp] aiohttp pyyaml python-dateutil
```

## Configuración

### Archivo de configuración (config.yaml)

Antes de ejecutar la aplicación, edita el archivo `config.yaml`:

```yaml
# Ejemplo de configuración básica
api:
  graphql_endpoint: "https://tu-api.com/graphql"  # Tu endpoint GraphQL
  api_key: "tu-api-key-aqui"                      # Clave API si es necesaria

folders:
  downloads: "downloads"        # Carpeta para ISOs descargados
  jdf_files: "jdf_files"       # Carpeta para archivos JDF
  completed: "completed"       # Trabajos completados
  failed: "failed"            # Trabajos fallidos

robot:
  burn_speed: "8x"            # Velocidad de quemado
  verify_after_burn: true     # Verificar después de quemar
```

### Parámetros importantes

- **graphql_endpoint**: URL de tu API GraphQL que proporciona los ISOs
- **api_key**: Clave de autenticación (si es necesaria)
- **max_concurrent**: Número máximo de trabajos simultáneos (recomendado: 1-3)
- **check_interval**: Frecuencia de verificación de nuevos ISOs (en segundos)

## Uso

### Ejecución básica

```bash
cd /Users/jorgejuarez/CascadeProjects/epson-burner-app
python main.py
```

### Funcionamiento

1. **Inicio**: La aplicación se inicia minimizada en la bandeja del sistema
2. **Verificación automática**: Consulta periódicamente la API GraphQL en busca de nuevos ISOs
3. **Descarga**: Descarga automáticamente los nuevos ISOs encontrados
4. **Procesamiento**: Genera archivos JDF y los coloca en la carpeta correspondiente
5. **Quemado**: El robot EPSON PP-100 lee los archivos JDF y realiza el quemado

### Interfaz de usuario

#### Ventana principal

- **Lista de trabajos**: Muestra todos los trabajos con su estado y progreso
- **Filtros**: Filtrar por estado (pendientes, quemando, completados, etc.)
- **Detalles del trabajo**: Información detallada del trabajo seleccionado
- **Controles**: Botones para actualizar, limpiar completados, etc.

#### Bandeja del sistema

- **Clic derecho**: Menú contextual con opciones
- **Doble clic**: Muestra/oculta la ventana principal
- **Notificaciones**: Informa sobre trabajos completados o fallidos

### Estados de los trabajos

- **Pendiente**: Trabajo creado pero no iniciado
- **Descargando**: Descargando el archivo ISO
- **Descargado**: ISO descargado, listo para generar JDF
- **Generando JDF**: Creando archivo JDF para el robot
- **Listo para quemar**: JDF generado, esperando al robot
- **Quemando**: Proceso de quemado en progreso
- **Verificando**: Verificación del disco quemado
- **Completado**: Trabajo terminado exitosamente
- **Fallido**: Error durante el proceso
- **Cancelado**: Trabajo cancelado por el usuario

## API GraphQL

### Consulta de nuevos ISOs

La aplicación espera una consulta GraphQL con la siguiente estructura:

```graphql
query GetNewIsos($lastCheckTime: String) {
  newIsos(lastCheckTime: $lastCheckTime) {
    id
    filename
    fileSize
    downloadUrl
    checksum
    createdAt
    description
    projectId
    priority
  }
}
```

### Campos requeridos

- `id`: Identificador único del ISO
- `filename`: Nombre del archivo
- `downloadUrl`: URL para descargar el archivo
- `fileSize`: Tamaño del archivo en bytes (opcional, para verificación)
- `checksum`: Hash del archivo (opcional, formato: "md5:checksum")

### Parámetros opcionales

- `lastCheckTime`: Timestamp ISO 8601 para filtrar ISOs nuevos
- `description`: Descripción del ISO
- `projectId`: ID del proyecto relacionado
- `priority`: Prioridad (LOW, NORMAL, HIGH, URGENT)

## Archivos JDF

### Estructura básica

Los archivos JDF generados siguen el estándar CIP4 JDF 1.3 y contienen:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<JDF xmlns:jdf="http://www.CIP4.org/JDFSchema_1_1" ID="job_id" Type="Product" Version="1.3" Status="Waiting">
  <Description Name="Disc Burn Job - filename.iso"/>
  <ResourcePool>
    <Component ID="Component_1" Class="Consumable" Status="Available">
      <ComponentType>Disc</ComponentType>
    </Component>
    <DigitalPrintingParams ID="DigitalAsset_1" Class="Parameter" Status="Available">
      <FileSpec URL="file:///path/to/iso/file.iso"/>
    </DigitalPrintingParams>
    <BurningParams ID="BurningParams_1" Class="Parameter" Status="Available">
      <BurnSpeed>8x</BurnSpeed>
      <Verification>true</Verification>
    </BurningParams>
  </ResourcePool>
  <Process ID="Process_1" Types="Burning">
    <Input>
      <ResourceReference rRef="Component_1"/>
      <ResourceReference rRef="DigitalAsset_1"/>
    </Input>
    <Parameter>
      <ResourceReference rRef="BurningParams_1"/>
    </Parameter>
  </Process>
</JDF>
```

### Ubicación de archivos

- **Archivos JDF**: Se generan en la carpeta `jdf_files/`
- **ISOs descargados**: Se almacenan en `downloads/`
- **Completados**: Se mueven a `completed/` después del éxito
- **Fallidos**: Se mueven a `failed/` en caso de error

## Mantenimiento

### Limpieza automática

La aplicación realiza automáticamente:

- Limpieza de trabajos antiguos (mayores a 7 días)
- Rotación de archivos de log
- Respaldos de base de datos
- Limpieza de descargas antiguas

### Respaldos

- **Base de datos**: Se crean respaldos automáticos diariamente
- **Configuración**: Copia de seguridad del archivo `config.yaml`
- **Logs**: Rotación automática cuando superan el tamaño máximo

### Monitoreo

#### Estado del sistema

Usa el menú de la bandeja del sistema > "Estado del sistema" para ver:

- Número de trabajos en cada estado
- Estadísticas de almacenamiento
- Próxima verificación de API
- Información general del sistema

#### Logs

Los logs se almacenan en `burner.log` con información detallada sobre:

- Errores de conexión API
- Progreso de descargas
- Estados de trabajos
- Errores del sistema

## Solución de problemas

### Problemas comunes

1. **Error de conexión API**
   - Verificar URL del endpoint GraphQL
   - Comprobar clave API si es necesaria
   - Revisar conectividad de red

2. **Trabajos atascados**
   - Reiniciar la aplicación
   - Verificar permisos de carpetas
   - Comprobar espacio en disco

3. **Archivos JDF no reconocidos por el robot**
   - Verificar configuración de quemado
   - Comprobar formato del archivo ISO
   - Revisar logs para errores específicos

### Logs de depuración

Para obtener más información, cambia el nivel de logging en `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

### Soporte

Para problemas técnicos:

1. Revisa los logs en `burner.log`
2. Verifica la configuración en `config.yaml`
3. Comprueba la conectividad con la API GraphQL
4. Reinicia la aplicación si es necesario

## Desarrollo

### Estructura del proyecto

```
epson-burner-app/
├── main.py                 # Punto de entrada principal
├── config.py               # Gestión de configuración
├── config.yaml             # Archivo de configuración
├── requirements.txt        # Dependencias Python
├── gui/
│   └── main_window.py      # Ventana principal de la interfaz
├── graphql_client.py       # Cliente GraphQL para API
├── iso_downloader.py       # Gestor de descargas de ISO
├── jdf_generator.py        # Generador de archivos JDF
├── job_queue.py            # Sistema de cola de trabajos
├── background_worker.py    # Trabajador en segundo plano
├── local_storage.py        # Almacenamiento local (SQLite)
└── burner_jobs.db          # Base de datos (se crea automáticamente)
```

### Extensión

Para agregar funcionalidades:

1. **Nueva fuente de ISOs**: Modificar `graphql_client.py`
2. **Nuevo formato de quemado**: Extender `jdf_generator.py`
3. **Nueva interfaz**: Agregar componentes en `gui/`
4. **Nuevos tipos de trabajo**: Extender `job_queue.py`

## Licencia

Este proyecto es desarrollado para uso específico con el robot EPSON PP-100. Consulta con el proveedor para requisitos de licencia específicos.

## Versión

Versión 1.0 - Aplicación inicial para gestión de quemado de discos con robot EPSON PP-100.
