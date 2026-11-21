# Proposal

## Why

El cliente y el mecánico asignado necesitan intercambiar mensajes sobre una orden desde el propio sistema. Un chat sencillo dentro de cada orden conservará la conversación para que ambos puedan consultarla cuando regresen a su detalle.

## What Changes

- Se guarda cada mensaje con su orden, autor y fecha.
- Se muestra el historial y un formulario sencillo en el detalle de la orden.
- El cliente propietario y el mecánico asignado pueden enviar mensajes; administradores y asesores pueden consultarlos en modo de solo lectura.
- Los mensajes se muestran al recargar la página; no se necesita entrega en tiempo real.
- El enlace público de seguimiento sigue siendo de solo consulta y no expone el chat.

## Capabilities

### New Capabilities

- `order-chat`: Chat persistente y sencillo por orden entre el cliente propietario y el mecánico asignado.

### Modified Capabilities

- `role-based-access`: Se amplían las reglas de acceso a los mensajes de una orden según el rol y la asignación.
- `workshop-management`: La ficha de una orden incorpora comunicación asociada a su presupuesto, evidencias y estado.

## Impact

- Django: modelo y migración de mensajes, vista POST, permisos y pruebas.
- Interfaz: historial y formulario de mensajes en la plantilla de detalle de orden.
- No se requieren dependencias adicionales ni infraestructura de WebSocket.
- Base de datos: historial persistente relacionado con cada orden y con el usuario autor.
