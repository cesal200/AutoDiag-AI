# AutoDiag AI - Sistema de Taller Mecánico con Pre-Diagnóstico IA

AutoDiag AI es una aplicación web desarrollada en Django para gestionar el flujo de trabajo de un taller mecánico con diagnóstico asistido por inteligencia artificial. El sistema permite registrar órdenes de servicio, capturar síntomas del cliente, analizar fallas con IA, generar reportes PDF y distribuir información por Telegram o correo electrónico.

## Índice

- [Descripción general](#descripción-general)
- [Objetivos del proyecto](#objetivos-del-proyecto)
- [Funcionalidades principales](#funcionalidades-principales)
- [Tecnologías utilizadas](#tecnologías-utilizadas)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Requisitos previos](#requisitos-previos)
- [Instalación y configuración](#instalación-y-configuración)
- [Ejecución de la aplicación](#ejecución-de-la-aplicación)
- [Rutas principales](#rutas-principales)
- [Flujo de trabajo](#flujo-de-trabajo)
- [Documentación adicional](#documentación-adicional)
- [Notas de desarrollo](#notas-de-desarrollo)

## Descripción general

Este proyecto nace para mejorar la eficiencia operativa de talleres automotrices, especialmente en la recepción y triage inicial de vehículos. En muchos talleres, el cliente describe un síntoma de forma imprecisa (ruidos, vibraciones, luces, fallas eléctricas, humo, etc.), lo que genera retrasos y errores al diagnosticar el problema.

AutoDiag AI busca reducir ese tiempo de atención con un proceso inteligente que:

- recibe la información del vehículo y del cliente,
- analiza síntomas usando IA,
- propone causas probables con niveles de riesgo,
- recomienda pruebas de taller,
- gestiona la orden de trabajo,
- genera reportes ejecutivos y técnicos en PDF,
- distribuye el reporte por los canales elegidos.

## Objetivos del proyecto

1. Automatizar la revisión preliminar de fallas mecánicas.
2. Reducir el tiempo de recepción en taller.
3. Mejorar la trazabilidad de las órdenes de trabajo.
4. Integrar información multimodal, como texto, imágenes y audio.
5. Generar reportes profesionales para clientes y coordinación interna.
6. Crear una base para futuras integraciones con IA, Telegram y correos automáticos.

## Funcionalidades principales

### 1. Gestión de órdenes de trabajo
- Registro de cliente y vehículo.
- Estado de la orden.
- Historial y seguimiento.
- Asignación de mecánicos y tareas.

### 2. Pre-diagnóstico con IA
- Captura de síntomas del cliente.
- Análisis de texto, imagen y audio.
- Normalización de fallas.
- Causas probables y su probabilidad.
- Nivel de riesgo del vehículo.
- Recomendaciones de pruebas técnicas.

### 3. Reportes PDF
- Generación automática de informes de taller.
- Plantillas HTML para exportación PDF.
- Visualización de vehículo, diagnóstico y presupuesto.

### 4. Distribución de reportes
- Envío por Telegram.
- Envío por correo electrónico.
- Posibilidad de descargar o enviar a ambos canales.

### 5. Panel administrativo
- Gestión de órdenes, usuarios y configuración.
- Configuración de servicios externos para distribución.

## Tecnologías utilizadas

- Python 3.13+
- Django 6.1+
- SQLite (base de datos por defecto)
- HTML / CSS / JavaScript
- xhtml2pdf para generación de PDF
- Pillow para manejo de imágenes
- ReportLab y pypdf para soporte de documentos
- Python-dotenv para configuración de entorno

## Estructura del proyecto

```text
proyectoadakedmy/
├── README.md
├── openspec/
│   ├── changes/
│   ├── config.yaml
│   └── specs/
├── taller_mecanico/
│   ├── ai_diagnosis/
│   ├── diagnostico_ia/
│   ├── distribucion/
│   ├── docs/
│   ├── reportes/
│   ├── reports/
│   ├── taller_mecanico/
│   ├── templates/
│   ├── workshop/
│   ├── db.sqlite3
│   ├── manage.py
│   ├── requirements.txt
│   ├── setup.bat
│   └── start_django.bat
└── Arquitectura Técnica - Sistema de Taller Mecánico con Pre-Diagnóstico IA.pdf
```

### Descripción de módulos principales

- `workshop/`: gestión de órdenes y flujo de taller.
- `diagnostico_ia/`: lógica de análisis inteligente del síntoma.
- `distribucion/`: flujo de envío y distribución de reportes.
- `taller_mecanico/`: configuración del proyecto Django y rutas globales.
- `templates/`: plantillas HTML reutilizables y páginas del sistema.
- `docs/`: documentación complementaria del proyecto.
- `openspec/`: especificación del sistema y cambios funcionales estructurados.

## Requisitos previos

Antes de ejecutar el proyecto, asegúrate de tener instalado:

- Python 3.11 o superior
- pip
- Git
- Un entorno virtual recomendado

## Instalación y configuración

1. Entrar al proyecto:

```bash
cd taller_mecanico
```

2. Crear y activar un entorno virtual:

```bash
python -m venv venv
```

En Windows:

```bash
venv\Scripts\activate
```

En Linux/macOS:

```bash
source venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Verificar que Django quedó instalado correctamente:

```bash
python -m django --version
```

5. Crear migraciones si el proyecto evoluciona a modelos reales:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Ejecución de la aplicación

Desde la carpeta del proyecto:

```bash
cd taller_mecanico
python manage.py runserver
```

La aplicación estará disponible en:

- http://127.0.0.1:8000/

También puedes iniciar usando el script incluido:

```bash
start_django.bat
```

## Rutas principales

El proyecto cuenta con rutas principales para acceder a los módulos clave:

```text
/                     -> Inicio del sistema
/workshop/orden/nueva/    -> Crear nueva orden
/workshop/orden/lista/    -> Lista de órdenes
/workshop/orden/<id>/     -> Detalle de orden
/api/diagnostico/analizar/<id>/   -> Diagnóstico IA
/api/diagnostico/resultado/<id>/  -> Resultado del análisis
/api/distribucion/configurar/<id>/ -> Configuración de entrega
/api/distribucion/enviar/<id>/     -> Envío de reporte
```

## Flujo de trabajo

1. El cliente solicita atención en el taller.
2. Se registra la orden con datos del vehículo y síntoma.
3. El sistema procesa la información con IA.
4. Se genera un diagnóstico probable:
   - causas,
   - riesgo,
   - pruebas sugeridas,
   - recomendaciones.
5. El técnico revisa la orden y cambia su estado.
6. Se genera un PDF del reporte.
7. El reporte se distribuye por Telegram, correo o ambos.

## Documentación adicional

Este proyecto incluye documentación complementaria en:

- `taller_mecanico/docs/usuario_informacion.md`
- `openspec/changes/...` para la especificación funcional y cambios del sistema

## Notas de desarrollo

- El proyecto está en una etapa inicial de implementación funcional.
- La base de datos actual es SQLite para facilitar desarrollo local y pruebas.
- El sistema ya tiene una estructura base para varios módulos, pero aún puede requerir más integración real con IA, almacenamiento persistente y APIs externas.
- Los templates y las vistas están listas para continuar ampliando la experiencia de usuario web.

## Siguiente evolución recomendada

- Conectar modelos reales de base de datos.
- Implementar autenticación de usuarios y roles.
- Integrar un modelo de IA real para diagnóstico multimodal.
- Generar PDF desde información real almacenada.
- Añadir envío real por Telegram y SMTP.
- Añadir panel administrativo con CRUD completo.

## Licencia

Este proyecto se entrega como desarrollo local de aplicación interna para taller mecánico. Si se va a distribuir en un entorno profesional, se recomienda revisar la licencia adecuada antes de su uso comercial o publicación pública.
