# AutoDiag AI - Información de Usuario

## Configuración Inicial

Para iniciar sesión y utilizar AutoDiag AI, siga estos pasos:

### 1. Creación de Cuenta Administrador

El sistema incluye una cuenta administrativa por defecto. Para acceder:

- **URL de acceso**: `http://127.0.0.1:8000/admin/`
- **Usuario**: `admin`
- **Contraseña**: `admin123` (cambiar en producción)

### 2. Configuración de Claves y Servicios

Para que el sistema funcione completamente, configure las siguientes claves en el archivo `settings.py` o mediante el panel de administración:

#### Telegram Bot API
1. Hablar con `@BotFather` en Telegram
2. Ejecutar `/newbot` para crear un nuevo bot
3. Copiar el **TOKEN del bot** generado
4. En el panel de Administración > `ConfiguracionDistribucion`, agregar el token
5. Obtener el **Chat ID** conversando con el bot y usando `/getchatid`

#### Configuración SMTP (Email)
En `taller_mecanico/settings.py`:

```python
EMAIL_HOST = 'smtp.gmail.com'  # o su proveedor de email
EMAIL_PORT = 587
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-password-o-app-password'
EMAIL_USE_TLS = True
```

#### Configuración de la Base de Datos

La base de datos SQLite está configurada en `db.sqlite3`. Para cambiar a PostgreSQL o MySQL, modificar la sección `DATABASES` en `settings.py`.

## Interacción de la Aplicación

### Flujo de Trabajo Completo

1. **Registro de Vehículo**
   - Acceder al módulo "Registrar Vehículo"
   - Llenar datos: placa, marca, modelo, año, motor, kilometraje
   - Adjuntar fotos de testigos y fugas (opcional)
   - Grabar nota de voz describiendo el síntoma

2. **Análisis Multimodal IA**
   - El sistema procesa automáticamente:
     - Transcripción de voz (procesamiento de audio)
     - Análisis de imágenes adjuntas
     - Datos del vehículo (marca, modelo, año)
     - Narrativa del cliente
   - Resultado: Síntomas normalizados, causas probables con probabilidades, nivel de riesgo, pruebas sugeridas

3. **Gestión en Taller**
   - Asignar mecánico a la orden
   - Seguir el flujo de estado: PRE_DIAGNÓSTICO → EN_TALLER → ESPERA_REPUESTO → LISTO → ENTREGADO
   - Agregar ítems de presupuesto (repuestos y mano de obra)
   - Aprobar presupuesto con el cliente

4. **Generación y Distribución de Reportes**
   - Solicitar reporte PDF
   - El PDF incluye: datos de la orden, vehículo, análisis IA, evidencia (fotos, audio), presupuesto
   - Distribución automática:
     - **Telegram**: Seleccionar en el panel de distribución
     - **Email**: Configurar dirección de email destino
     - **Ambos**: Recibir el reporte en ambos canales
     - **Ninguno**: Descargar localmente

### Accesos Rápidos

| Acción | URL | Descripción |
|--------|-----|-------------|
| Panel Admin | `/admin/` | Gestión completa de órdenes, usuarios y configuración |
| Nueva Orden | `/workshop/orden/nueva/` | Formulario para registrar nuevo vehículo y síntoma |
| Lista de Órdenes | `/workshop/orden/lista/` | Ver todas las órdenes con su estado actual |
| Reporte PDF | `/reportes/generar/<id>/` | Generar y distribuir reporte PDF |
| API Endpoints | `/api/` | Endpoints REST para integraciones externas |

### Problemas Comunes

- **IA no responde**: Verificar que las claves de API de Telegram y servicios de IA estén configuradas
- **PDF no genera**: Confirmar que xhtml2pdf está instalado y las plantillas HTML son válidas
- **Correos no se envían**: Verificar configuración SMTP y credenciales
- **Telegram no entrega**: Verificar el Chat ID y que el bot tiene permisos para enviar documentos

### Límites y Consideraciones

- Tamaño máximo de foto: 5MB
- Tamaño máximo de audio: 10MB
- Tiempo máximo de generación de PDF: 30 segundos
- Máximo 3 causas probables por análisis
- Niveles de riesgo: PUEDE_RODAR, PRECAUCION, NO_MOVER_GRUA

## Próximos Pasos

1. Personalizar las plantillas HTML para PDFs con la identidad de su taller
2. Entrenar o configurar el modelo de IA con datos locales
3. Capacitar al personal en el uso del panel de administración
4. Configurar backups automáticos de la base de datos
5. Implementar notificaciones push adicionales

---

*Versión 1.0 - AutoDiag AI Sistema de Taller Mecánico con Pre-Diagnóstico IA*
*Basado en la especificación: "Arquitectura Técnica - Sistema de Taller Mecánico con Pre-Diagnóstico IA"*