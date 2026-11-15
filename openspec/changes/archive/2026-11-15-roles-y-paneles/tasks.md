# Tasks

## 1. Roles y base de datos

- [x] 1.1 Crear la app `accounts` con `PerfilUsuario` (roles ADMIN/ASESOR/MECANICO/CLIENTE), helpers y signal `post_save`; verificar con `python manage.py check`
- [x] 1.2 Registrar `accounts` en `INSTALLED_APPS` y añadir la migración inicial de `accounts`; verificar con `python manage.py makemigrations accounts`
- [x] 1.3 Crear la migración de datos que asigna ADMIN a superusuarios, ASESOR a staff y CLIENTE al resto; verificar que `python manage.py migrate` termina sin errores
- [x] 1.4 Extender `OrdenFalla` con `cliente` nullable, datos walk-in, timestamps y `cliente_efectivo`; verificar con `python manage.py makemigrations workshop`
- [x] 1.5 Implementar generación real de `codigo_orden`, token público con expiración y validación de transiciones; verificar con las pruebas de modelos de la tarea 6.2

## 2. Autenticación y registro

- [x] 2.1 Configurar `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` y las rutas de `django.contrib.auth.urls`; verificar con `python manage.py check`
- [x] 2.2 Implementar `rol_requerido` y el mixin de rol en `accounts/decorators.py`; verificar que el test de acceso anónimo redirige y el de rol incorrecto devuelve 403
- [x] 2.3 Implementar el registro público que siempre asigna CLIENTE y su plantilla `accounts/registro.html`; verificar que el test de registro privilegiado crea un CLIENTE
- [x] 2.4 Crear `registration/login.html` con el estilo existente y enlazar login/registro/logout en `base.html`; verificar que el login manual redirige a `/panel/`
- [x] 2.5 Registrar `PerfilUsuario` en el admin de Django con inline en `UserAdmin`; verificar que `/admin/` permite editar el rol

## 3. Órdenes y permisos

- [x] 3.1 Crear `workshop/forms.py` con formularios de orden, evidencia, ítem de presupuesto, cambio de estado y cliente rápido; verificar con `python manage.py check`
- [x] 3.2 Refactorizar `orden_lista` con querysets filtrados por rol; verificar que los tests de aislamiento de cliente y técnico pasan
- [x] 3.3 Refactorizar `orden_nueva` para persistir órdenes reales y asignar el cliente autenticado; verificar que el cliente crea una orden y el técnico recibe 403
- [x] 3.4 Añadir permisos de objeto a `orden_detalle` y `generar_pdf`; verificar que abrir una orden ajena devuelve 403
- [x] 3.5 Implementar cambio de estado, asignación de mecánico, creación de ítems y aprobación de presupuesto con sus permisos; verificar que las pruebas de autorización pasan
- [x] 3.6 Actualizar `workshop/admin.py` para listar y filtrar por cliente, mecánico y estado; verificar que las órdenes walk-in aparecen en `/admin/`

## 4. Walk-in y seguimiento público

- [x] 4.1 Implementar el flujo de orden walk-in con `cliente` nulo y nombre/teléfono obligatorio cuando no hay cliente; verificar que el test de walk-in crea la orden y el test sin identificación falla
- [x] 4.2 Implementar la creación rápida de cliente desde el panel de ADMIN/ASESOR con email único y contraseña inutilizable; verificar que el duplicado se rechaza
- [x] 4.3 Implementar la vista pública `seguimiento/<uuid:token>/` con validación de expiración y su plantilla; verificar los tests de token válido y token expirado/desconocido
- [x] 4.4 Implementar la regeneración de token para ADMIN/ASESOR; verificar que el token anterior deja de resolver

## 5. Paneles y navegación

- [x] 5.1 Implementar `/panel/` con redirección por rol y los paneles de admin, cliente y técnico con datos reales; verificar que cada rol llega a su panel
- [x] 5.2 Ajustar `base.html` y `home.html` para mostrar navegación y acciones según sesión y rol; verificar manualmente que un cliente no ve enlaces de administración
- [x] 5.3 Mostrar acciones contextuales en el detalle de la orden según rol (estado, mecánico, presupuesto, token, PDF); verificar con los tres usuarios del seed

## 6. Datos demo, pruebas e integración

- [x] 6.1 Crear el comando `seed_demo` con usuarios admin/cliente/técnico y órdenes de ejemplo, incluida una walk-in; verificar ejecutándolo dos veces sin duplicados
- [x] 6.2 Escribir pruebas de modelos (código, transiciones, token, walk-in) y de roles/permisos; verificar con `python manage.py test`
- [x] 6.3 Ejecutar `python manage.py check`, `makemigrations --check`, `migrate` y la suite completa; verificar que todo termina sin errores
- [x] 6.4 Ejecutar el servidor y recorrer manualmente login, panel de cada rol, alta walk-in, portal por token y cierre de sesión; verificar el flujo completo

## Workflow follow-up

- Revisar los artefactos OpenSpec y archivar el cambio con `openspec archive roles-y-paneles` cuando la implementación esté validada.
