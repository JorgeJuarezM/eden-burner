# 📝 Guía de Plantillas - EPSON PP-100 Disc Burner

Esta guía explica cómo funcionan y personalizar las plantillas utilizadas por la aplicación para generar archivos JDF, etiquetas de disco y archivos de datos.

## 🎯 Visión General

La aplicación utiliza un sistema de plantillas basado en Jinja2 que permite generar archivos personalizados con información dinámica del paciente, estudio y configuración del sistema.

## 📁 Ubicación de Plantillas

Las plantillas se encuentran en la carpeta `templates/`:

```
templates/
├── jdf_template.jdf      # Plantilla para archivos JDF del robot
├── default.tdd           # Plantilla para carátulas de disco
└── template.data         # Plantilla para archivos de datos estructurados
```

## 🔧 Variables Disponibles

Todas las plantillas tienen acceso a las siguientes variables:

### Información del Paciente
- `{{patient_name}}` - Nombre completo del paciente
- `{{patient_id}}` - ID único del paciente
- `{{study_date}}` - Fecha del estudio (YYYY-MM-DD)
- `{{study_description}}` - Descripción del estudio médico

### Información del Trabajo
- `{{job_id}}` - ID único del trabajo de quemado
- `{{volume_label}}` - Etiqueta del volumen del disco
- `{{disc_type}}` - Tipo de disco (CD/DVD)
- `{{current_date}}` - Fecha y hora actual de generación

### Configuración Técnica
- `{{burn_speed}}` - Velocidad de quemado configurada
- `{{verify_after_burn}}` - Si se verifica después de quemar (true/false)
- `{{robot_name}}` - Nombre del robot EPSON
- `{{robot_uuid}}` - UUID único del robot

### Rutas de Archivos
- `{{iso_path}}` - Ruta completa al archivo ISO
- `{{jdf_path}}` - Ruta al archivo JDF generado
- `{{label_path}}` - Ruta al archivo de etiqueta generado

## 📋 Plantillas Específicas

### 1. Plantilla JDF (`jdf_template.jdf`)

Esta plantilla genera el archivo de instrucciones para el robot EPSON PP-100.

**Ejemplo de uso:**
```jdf
DISC_TYPE={{disc_type}}
FORMAT=JOLIET
IMAGE={{iso_path}}
VOLUME_LABEL={{volume_label}}
LABEL={{label_path}}
REPLACE_FIELD={{data_path}}
PUBLISHER={{robot_name}}
COPIES=1
```

### 2. Plantilla de Carátula (`default.tdd`)

Genera la información de diseño para imprimir en la carátula del disco.

**Ejemplo de uso:**
```tdd
# Información básica del disco
DISC_TITLE={{patient_name}}
DISC_LABEL={{job_id}}
DISC_TYPE={{disc_type}}

# Configuración de impresión
PRINT_QUALITY=HIGH
PRINT_MODE=COLOR
BACKGROUND_COLOR=WHITE

# Elementos de diseño
TEXT_ELEMENT_1={{patient_name}}
TEXT_ELEMENT_2={{study_date}}
TEXT_ELEMENT_3={{study_description}}

# Configuración de posición
TEXT_1_X=0
TEXT_1_Y=10
TEXT_1_FONT=ARIAL
TEXT_1_SIZE=12
TEXT_1_COLOR=BLACK
```

### 3. Plantilla de Datos (`template.data`)

Genera información estructurada para auditoría y seguimiento.

**Ejemplo de uso:**
```data
PatientName={{patient_name}}
StudyDate={{study_date}}
StudyDescription={{study_description}}
DiscID={{job_id}}
BurnSpeed={{burn_speed}}
RobotName={{robot_name}}
ISOPath={{iso_path}}
CreationDate={{current_date}}
```

## 🛠️ Personalización Avanzada

### Variables Condicionales

Puedes usar lógica condicional en las plantillas:

```jdf
{% if patient_name %}
PATIENT_NAME={{patient_name}}
{% else %}
PATIENT_NAME=Paciente Desconocido
{% endif %}
```

### Bucles

Para elementos repetitivos:

```jdf
{% for item in study_items %}
ITEM_{{ loop.index }}={{ item }}
{% endfor %}
```

### Filtros

Aplicar formato a las variables:

```jdf
CREATION_DATE={{ current_date|date('Y-m-d H:i:s') }}
PATIENT_NAME={{ patient_name|upper }}
```

## 🔍 Ejemplos Prácticos

### Plantilla JDF Completa

```jdf
# Archivo JDF generado automáticamente
DISC_TYPE={{disc_type}}
FORMAT=JOLIET
IMAGE={{iso_path}}
VOLUME_LABEL={{patient_name}} - {{study_date}}
LABEL={{label_path}}
REPLACE_FIELD={{data_path}}
PUBLISHER={{robot_name}}
COPIES=1

# Información del paciente
PATIENT_ID={{patient_id}}
STUDY_DESCRIPTION={{study_description}}
ROBOT_UUID={{robot_uuid}}
GENERATION_DATE={{current_date}}
```

### Plantilla de Carátula con Diseño

```tdd
# Carátula del disco médico
DISC_TITLE=Estudio Médico
DISC_SUBTITLE={{patient_name}}
DISC_DATE={{study_date}}

# Información del estudio
MODALITY={{modality}}
DESCRIPTION={{study_description}}

# Diseño de la etiqueta
BACKGROUND_IMAGE=fondo_medico.png
TEXT_COLOR=BLUE
FONT_SIZE=14
POSITION_CENTER_X=0
POSITION_CENTER_Y=0
```

## 🚨 Consideraciones Importantes

### Codificación de Caracteres
- Las plantillas deben estar en UTF-8
- Manejar caracteres especiales del paciente correctamente

### Validación de Datos
- Verificar que las variables críticas estén disponibles
- Proporcionar valores por defecto para campos opcionales

### Seguridad
- No exponer información sensible del paciente
- Validar contenido antes de escribir archivos

## 🔧 Solución de Problemas

### Problema: Variable no definida
**Solución:** Agregar verificación en la plantilla:
```jdf
{% if patient_name is defined %}
PATIENT={{patient_name}}
{% endif %}
```

### Problema: Formato incorrecto
**Solución:** Verificar sintaxis Jinja2:
```jdf
{# Comentario #}
{{ variable|default('valor_por_defecto') }}
```

## 📞 Soporte

Para personalizaciones avanzadas o problemas con plantillas, consultar la [Guía de Desarrollo](../DEVELOPMENT_README.md) o contactar al equipo de desarrollo.
