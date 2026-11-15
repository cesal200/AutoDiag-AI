# AutoDiag AI - Manual de Usuario y Operación

## 1. Requisitos

- Python 3.11 o superior.
- Dependencias de `taller_mecanico/requirements.txt`.
- Base de datos SQLite para desarrollo local (configurable en `settings.py`).
- Navegador moderno con acceso a `http://127.0.0.1:8000/`.

## 2. Instalación rápida

```powershell
cd taller_mecanico
..\.venv\Scripts\Activate.ps1
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py seed_demo
..\.venv\Scripts\python.exe manage.py runserver
```

Edite `.env` antes de usar servicios externos. El archivo `.env` no debe subirse al repositorio.

## 3. Variables de entorno

| Variable | Uso |
|----------|-----|
| `DJANGO_SECRET_KEY` | Clave secreta de Django. Obligatoria en producción. |
| `DJANGO_DEBUG` | `1` para desarrollo, `0` en producción. |
| `DJANGO_ALLOWED_HOSTS` | Hosts separados por coma. |
| `OPENAI_API_KEY` | Opcional. Habilita Whisper y visión con OpenAI. |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram. |
| `TELEGRAM_CHAT_ID` | Chat por defecto cuando la orden no define uno. |
| `EMAIL_BACKEND` | Backend SMTP o de consola. |
| `EMAIL_HOST`, `EMAIL_PORT` | Servidor y puerto SMTP. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Credenciales SMTP. |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | Seguridad de la conexión SMTP. |
| `DEFAULT_FROM_EMAIL` | Remitente de los reportes. |

Compruebe la configuración de distribución con:

```powershell
..\.venv\Scripts\python.exe manage.py check_distribucion
```

El comando no envía reportes: valida el token de Telegram con `getMe` y abre/cierra la conexión SMTP.

## 4. Acceso y usuarios demo

- Login: `http://127.0.0.1:8000/accounts/login/`
- Administración Django: `http://127.0.0.1:8000/admin/`

Después de `seed_demo`:

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `admin` | `demo12345` | Administrador / superusuario |
| `asesor` | `demo12345` | Asesor operativo |
| `tecnico` | `demo12345` | Mecánico |
| `cliente` | `demo12345` | Cliente |

Cambie estas contraseñas antes de cualquier despliegue real.

## 5. Roles y permisos

- **ADMIN**: acceso completo, incluido el admin de Django y la regeneración de tokens públicos.
- **ASESOR**: gestión operativa de órdenes, clientes, presupuestos, PDF y distribución; sin admin de Django.
- **MECANICO**: solo órdenes asignadas; puede cambiar estado, registrar evidencias y gestionar presupuesto.
- **CLIENTE**: solo sus propias órdenes; puede consultar el seguimiento público y aprobar ítems del presupuesto.

Las órdenes walk-in permiten registrar un cliente sin cuenta con nombre y teléfono.

## 6. Flujo operativo

1. **Registrar vehículo** en `/workshop/vehiculo/nuevo/` con placa, marca, modelo, año, motor y cliente.
2. **Crear orden** en `/workshop/orden/nueva/`. El sistema genera `OR-YYYY-NNN` y estado `PRE_DIAGNOSTICO`.
3. **Registrar evidencia** desde el detalle de la orden: narrativa, audio y/o imagen.
4. **Análisis IA** desde `/api/diagnostico/analizar/<orden_id>/`. El resultado muestra síntomas normalizados, tres causas con probabilidad, riesgo y pruebas sugeridas.
5. **Asignar mecánico** desde el detalle de la orden.
6. **Gestionar estado**: `PRE_DIAGNOSTICO → EN_TALLER → ESPERA_REPUESTO → LISTO → ENTREGADO`.
7. **Presupuesto**: agregar repuestos y mano de obra; el cliente puede aprobar cada ítem.
8. **PDF**: previsualizar en `/workshop/pdf/<orden_id>/` y descargar en `/workshop/pdf/<orden_id>/descargar/`.
9. **Distribución**: configurar en `/api/distribucion/configurar/<orden_id>/` y enviar en `/api/distribucion/enviar/<orden_id>/`.

Toda orden genera un enlace público `seguimiento/<token>/`; el administrador puede regenerarlo.

## 7. Pre-diagnóstico IA

### Motor local

Sin `OPENAI_API_KEY`, el sistema usa una taxonomía determinista en `diagnostico_ia/taxonomy.py`:

- Detecta componentes por palabras clave en español.
- Normaliza síntomas con códigos como `FRENOS-01` o `MOTOR-02`.
- Genera exactamente tres causas ordenadas por probabilidad.
- Ajusta el riesgo según palabras y componentes detectados.
- Propone pruebas con procedimiento y valor esperado.

### OpenAI opcional

Con `OPENAI_API_KEY`:

- Whisper transcribe notas de voz en español (`whisper-1`).
- Un modelo de visión describe fotos de evidencia (`gpt-4o-mini`).
- Ante cualquier error de red, cuota o API, se usa el resultado local sin bloquear la orden.

### Límites y criterios de riesgo

- **PUEDE_RODAR**: síntomas leves sin indicios de falla crítica.
- **PRECAUCION**: se recomienda movilizar el vehículo solo para inspección cercana.
- **NO_MOVER_GRUA**: se detectaron frenos, dirección, sobrecalentamiento, humo, fugas críticas u otra señal de alto riesgo.

Limitaciones importantes:

- La taxonomía local es orientativa y **no sustituye** la inspección de un mecánico certificado.
- Las probabilidades son relativas al ranking, no diagnósticos confirmados.
- La transcripción local no está habilitada; si no hay OpenAI, se usa la narrativa escrita.
- La confianza de transcripción se guarda en `transcripcion_confianza`; con Whisper se reporta `0.9`, sin servicio queda en `0.0`.
- La descripción local de imágenes solo reporta dimensiones y brillo; un modelo de visión externo es necesario para reconocer componentes.
- La precisión mínima del 90% en voz depende de la calidad del audio y del servicio externo; valide siempre el resultado.

## 8. PDF

El informe se genera con `xhtml2pdf` desde `templates/pdf/informe_taller.html`. Incluye:

- Datos de orden, taller, cliente y vehículo.
- Kilometraje, estado y fechas.
- Evidencias y análisis IA más reciente.
- Presupuesto con total y estado de aprobación.

Las pruebas automatizadas verifican que el PDF se genere en menos de 30 segundos y que funcione con y sin datos opcionales.

## 9. Distribución

Cada orden puede usar:

- **Telegram**: requiere `TELEGRAM_BOT_TOKEN` y un `chat_telegram_id` en la configuración de la orden o `TELEGRAM_CHAT_ID`.
- **Email**: requiere SMTP configurado y `email_destino`.
- **Ambos**: intenta los dos canales de forma independiente.
- **Ninguno**: deja disponible la descarga local.

Cada intento se registra en `EnvioReportes` con estado `Pendiente`, `Enviado` o `Fallido`. Los fallos se reintentan hasta tres veces con espera progresiva.

Para Telegram: cree un bot con `@BotFather`, copie el token y obtenga el chat ID escribiendo al bot o consultando `getUpdates`.

## 10. Problemas comunes

- **No se genera PDF**: revise `xhtml2pdf` instalado y ejecute las pruebas.
- **No hay transcripción**: configure `OPENAI_API_KEY` o utilice la narrativa escrita.
- **Telegram falla**: ejecute `check_distribucion`, confirme el chat ID y que el bot pueda enviar documentos.
- **Email falla**: confirme credenciales SMTP, TLS/SSL y que el remitente esté permitido.
- **Migraciones pendientes**: ejecute `python manage.py migrate`.
- **Datos demo dañados**: use una base limpia o actualice los vehículos/talleres existentes desde el admin.

## 11. Producción

- Use `DJANGO_DEBUG=0` y una `DJANGO_SECRET_KEY` robusta.
- Sirva archivos media y estáticos desde el servidor web, no desde Django.
- Ejecute `python manage.py migrate` en el entorno de producción.
- Configure HTTPS y copias de seguridad de la base de datos.
- No use las credenciales demo.

---

*Versión 1.1 - AutoDiag AI. Manual operativo del taller y del pre-diagnóstico IA.*
