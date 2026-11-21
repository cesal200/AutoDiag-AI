from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.decorators import rol_requerido
from accounts.models import PerfilUsuario
from accounts.permissions import (
    es_admin_operativo,
    es_cliente,
    es_tecnico,
    puede_editar_estado,
    puede_ver_orden,
    rol_de,
)
from diagnostico_ia.services import procesar_orden

from .forms import (
    AsignarMecanicoForm,
    CambioEstadoForm,
    ClienteRapidoForm,
    EvidenciaSintomaForm,
    ItemPresupuestoForm,
    MensajeOrdenForm,
    OrdenFallaForm,
    VehiculoForm,
)
from .models import ESTADO_CHOICES, OrdenFalla, Vehiculo
from .pdf import construir_pdf


@login_required
def orden_lista(request):
    ordenes = OrdenFalla.objects.select_related(
        'cliente', 'mecanico_asignado', 'vehiculo', 'taller'
    ).prefetch_related('etiquetas')
    rol = rol_de(request.user)

    if rol == PerfilUsuario.Rol.CLIENTE:
        ordenes = ordenes.filter(cliente=request.user)
    elif rol == PerfilUsuario.Rol.MECANICO:
        ordenes = ordenes.filter(mecanico_asignado=request.user)

    estado = request.GET.get('estado')
    if estado in dict(ESTADO_CHOICES):
        ordenes = ordenes.filter(estado=estado)

    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        ordenes = ordenes.filter(
            Q(codigo_orden__icontains=busqueda)
            | Q(ticket__icontains=busqueda)
            | Q(vehiculo__placa__icontains=busqueda)
            | Q(vehiculo__marca__icontains=busqueda)
            | Q(vehiculo__modelo__icontains=busqueda)
            | Q(cliente__username__icontains=busqueda)
            | Q(nombre_cliente_walkin__icontains=busqueda)
        )

    vehiculo = request.GET.get('vehiculo', '').strip()
    if vehiculo:
        ordenes = ordenes.filter(
            Q(vehiculo__placa__icontains=vehiculo)
            | Q(vehiculo__marca__icontains=vehiculo)
            | Q(vehiculo__modelo__icontains=vehiculo)
        )

    mecanico = request.GET.get('mecanico', '')
    if mecanico == 'sin_asignar':
        ordenes = ordenes.filter(mecanico_asignado__isnull=True)
    elif mecanico.isdigit():
        ordenes = ordenes.filter(mecanico_asignado_id=int(mecanico))

    return render(request, 'workshop/orden_lista.html', {
        'title': 'Órdenes',
        'ordenes': ordenes,
        'estados': ESTADO_CHOICES,
        'estado_actual': estado or '',
        'busqueda': busqueda,
        'vehiculo_actual': vehiculo,
        'mecanico_actual': mecanico,
        'mecanicos': User.objects.filter(perfil__rol=PerfilUsuario.Rol.MECANICO).order_by(
            'first_name', 'last_name', 'username'
        ),
        'es_admin_operativo': es_admin_operativo(request.user),
    })


@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR, PerfilUsuario.Rol.CLIENTE)
def orden_nueva(request):
    admin_operativo = es_admin_operativo(request.user)
    form = OrdenFallaForm(user=request.user)
    cliente_rapido_form = ClienteRapidoForm() if admin_operativo else None

    if request.method == 'POST':
        if 'crear_cliente_rapido' in request.POST:
            if not admin_operativo:
                raise PermissionDenied
            cliente_rapido_form = ClienteRapidoForm(request.POST)
            if cliente_rapido_form.is_valid():
                cliente = cliente_rapido_form.save()
                messages.success(request, f'Cliente {cliente.get_username()} creado.')
                return redirect(f"{reverse('orden_nueva')}?cliente={cliente.pk}")
        else:
            form = OrdenFallaForm(request.POST, user=request.user)
            if form.is_valid():
                orden = form.save(commit=False)
                if es_cliente(request.user):
                    orden.cliente = request.user
                orden.save()
                form.save_m2m()
                messages.success(
                    request,
                    'Orden creada. Comparte el enlace de seguimiento con el cliente.',
                )
                return redirect('orden_detalle', orden_id=orden.pk)
    else:
        initial = {}
        cliente_id = request.GET.get('cliente')
        if cliente_id and admin_operativo:
            initial['cliente'] = cliente_id
        vehiculo_id = request.GET.get('vehiculo')
        if vehiculo_id:
            initial['vehiculo'] = vehiculo_id
        form = OrdenFallaForm(initial=initial, user=request.user)

    return render(request, 'workshop/orden_nueva.html', {
        'title': 'Nueva orden',
        'subtitle': 'Registra un vehículo y el síntoma del cliente.',
        'form': form,
        'cliente_rapido_form': cliente_rapido_form,
        'es_admin_operativo': admin_operativo,
    })


@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR, PerfilUsuario.Rol.CLIENTE)
def vehiculo_nueva(request):
    initial = {}
    if es_cliente(request.user):
        initial['cliente'] = request.user
    form = VehiculoForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        vehiculo = form.save(commit=False)
        if es_cliente(request.user):
            vehiculo.cliente = request.user
        vehiculo.save()
        messages.success(request, f'Vehículo {vehiculo.placa} registrado.')
        return redirect(f"{reverse('orden_nueva')}?vehiculo={vehiculo.pk}")

    return render(request, 'workshop/vehiculo_nueva.html', {
        'title': 'Registrar vehículo',
        'form': form,
    })


@login_required
def orden_detalle(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related(
            'cliente', 'mecanico_asignado', 'vehiculo', 'taller'
        ).prefetch_related(
            'items_presupuesto', 'evidencias', 'etiquetas', 'analisis_ia',
            'mensajes__autor',
        ),
        pk=orden_id,
    )
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied

    admin_operativo = es_admin_operativo(request.user)
    tecnico_asignado = es_tecnico(request.user) and orden.mecanico_asignado_id == request.user.id
    cliente_dueno = orden.cliente_id == request.user.id
    puede_cambiar_estado = puede_editar_estado(request.user, orden)
    puede_operar = admin_operativo or tecnico_asignado
    puede_evidenciar = puede_operar or cliente_dueno
    config_distribucion = getattr(orden, 'config_distribucion', None)
    codigos_estado = [codigo for codigo, _ in ESTADO_CHOICES]
    indice_actual = codigos_estado.index(orden.estado)

    context = {
        'title': f'Orden {orden.codigo_orden}',
        'orden': orden,
        'es_admin_operativo': admin_operativo,
        'es_tecnico_asignado': tecnico_asignado,
        'es_cliente_dueno': cliente_dueno,
        'puede_cambiar_estado': puede_cambiar_estado,
        'puede_operar': puede_operar,
        'puede_evidenciar': puede_evidenciar,
        'form_estado': CambioEstadoForm(orden=orden) if puede_cambiar_estado else None,
        'form_mecanico': AsignarMecanicoForm(instance=orden) if admin_operativo else None,
        'form_item': ItemPresupuestoForm() if puede_operar else None,
        'form_evidencia': EvidenciaSintomaForm() if puede_evidenciar else None,
        'mensaje_form': MensajeOrdenForm(),
        'mensajes': orden.mensajes.select_related('autor').all(),
        'usuario_id': request.user.id,
        'ultimo_analisis': orden.analisis_ia.first(),
        'config_distribucion': config_distribucion,
        'workflow': [
            {
                'codigo': codigo,
                'etiqueta': etiqueta,
                'completado': indice <= indice_actual,
                'actual': indice == indice_actual,
            }
            for indice, (codigo, etiqueta) in enumerate(ESTADO_CHOICES)
        ],
        'total_presupuesto': sum(
            (item.subtotal for item in orden.items_presupuesto.all()), Decimal('0')
        ),
    }
    return render(request, 'workshop/orden_detalle.html', context)


@login_required
def mensajes_orden(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied
    mensajes = orden.mensajes.select_related('autor').all()
    return render(request, 'workshop/_mensajes_orden.html', {
        'mensajes': mensajes,
        'usuario_id': request.user.id,
    })


@login_required
@require_POST
def enviar_mensaje_orden(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied

    form = MensajeOrdenForm(request.POST)
    if form.is_valid():
        mensaje = form.save(commit=False)
        mensaje.orden = orden
        mensaje.autor = request.user
        mensaje.save()
        messages.success(request, 'Mensaje enviado al ticket.')
    else:
        messages.error(request, 'Escribe un mensaje antes de enviarlo.')
    return redirect('orden_detalle', orden_id=orden.pk)


@login_required
@require_POST
def cambiar_estado(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    if not puede_editar_estado(request.user, orden):
        raise PermissionDenied

    nuevo_estado = request.POST.get('estado', '')
    try:
        orden.cambiar_estado(nuevo_estado)
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if exc.messages else 'Transición no válida.')
    else:
        messages.success(request, f'Estado actualizado a {orden.get_estado_display()}.')
    return redirect('orden_detalle', orden_id=orden.pk)


@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR)
@require_POST
def asignar_mecanico(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    form = AsignarMecanicoForm(request.POST, instance=orden)
    if form.is_valid():
        form.save()
        if orden.mecanico_asignado_id:
            messages.success(request, f'Mecánico asignado: {orden.mecanico_asignado.get_username()}.')
        else:
            messages.info(request, 'Orden sin mecánico asignado.')
    else:
        messages.error(request, 'No se pudo asignar el mecánico.')
    return redirect('orden_detalle', orden_id=orden.pk)


@login_required
@require_POST
def agregar_item(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    es_tecnico_asignado = es_tecnico(request.user) and orden.mecanico_asignado_id == request.user.id
    if not (es_admin_operativo(request.user) or es_tecnico_asignado):
        raise PermissionDenied

    form = ItemPresupuestoForm(request.POST)
    if form.is_valid():
        item = form.save(commit=False)
        item.orden = orden
        item.save()
        messages.success(request, 'Ítem de presupuesto agregado.')
    else:
        messages.error(request, 'Revisa los datos del ítem de presupuesto.')
    return redirect('orden_detalle', orden_id=orden.pk)


@login_required
@require_POST
def eliminar_item(request, orden_id, item_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    es_tecnico_asignado = es_tecnico(request.user) and orden.mecanico_asignado_id == request.user.id
    if not (es_admin_operativo(request.user) or es_tecnico_asignado):
        raise PermissionDenied

    item = get_object_or_404(orden.items_presupuesto, pk=item_id)
    item.delete()
    messages.success(request, 'Ítem de presupuesto eliminado.')
    return redirect('orden_detalle', orden_id=orden.pk)


@login_required
@require_POST
def aprobar_item(request, orden_id, item_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    if orden.cliente_id != request.user.id:
        raise PermissionDenied

    item = get_object_or_404(orden.items_presupuesto, pk=item_id)
    item.aprobado_cliente = True
    item.save(update_fields=['aprobado_cliente'])
    messages.success(request, 'Ítem aprobado.')
    return redirect('orden_detalle', orden_id=orden.pk)


@login_required
@require_POST
def agregar_evidencia(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    es_tecnico_asignado = es_tecnico(request.user) and orden.mecanico_asignado_id == request.user.id
    cliente_dueno = orden.cliente_id == request.user.id
    if not (es_admin_operativo(request.user) or es_tecnico_asignado or cliente_dueno):
        raise PermissionDenied

    form = EvidenciaSintomaForm(request.POST, request.FILES)
    if form.is_valid():
        evidencia = form.save(commit=False)
        evidencia.orden = orden
        if cliente_dueno and not evidencia.nivel_riesgo:
            evidencia.nivel_riesgo = 'PRECAUCION'
        evidencia.save()
        try:
            procesar_orden(orden)
            messages.success(request, 'Evidencia registrada y analizada por IA.')
        except Exception:
            messages.success(request, 'Evidencia registrada.')
            messages.warning(request, 'El análisis IA no pudo completarse; puedes reintentarlo.')
    else:
        messages.error(request, 'Revisa los datos de la evidencia.')
    return redirect('orden_detalle', orden_id=orden.pk)


@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR)
def cliente_rapido(request):
    form = ClienteRapidoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cliente = form.save()
        messages.success(request, f'Cliente {cliente.get_username()} creado.')
        return redirect(f"{reverse('orden_nueva')}?cliente={cliente.pk}")

    return render(request, 'workshop/cliente_rapido.html', {
        'title': 'Crear cliente rápido',
        'form': form,
    })


@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR)
@require_POST
def regenerar_token(request, orden_id):
    orden = get_object_or_404(OrdenFalla, pk=orden_id)
    orden.regenerar_token()
    messages.success(request, 'Se generó un nuevo enlace de seguimiento.')
    return redirect('orden_detalle', orden_id=orden.pk)


@login_required
def generar_pdf(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('vehiculo', 'taller').prefetch_related(
            'items_presupuesto', 'etiquetas', 'evidencias', 'analisis_ia'
        ),
        pk=orden_id,
    )
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied

    return render(request, 'workshop/generar_pdf.html', {
        'title': f'Reporte {orden.codigo_orden}',
        'orden': orden,
        'analisis': orden.analisis_ia.first(),
        'total_presupuesto': orden.total_presupuesto,
    })


@login_required
def descargar_pdf(request, orden_id):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('vehiculo', 'taller').prefetch_related(
            'items_presupuesto', 'evidencias', 'analisis_ia'
        ),
        pk=orden_id,
    )
    if not puede_ver_orden(request.user, orden):
        raise PermissionDenied

    pdf = construir_pdf(orden)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="reporte-{orden.codigo_orden}.pdf"'
    )
    return response


def seguimiento_publico(request, token):
    orden = get_object_or_404(
        OrdenFalla.objects.select_related('cliente', 'mecanico_asignado').prefetch_related(
            'items_presupuesto', 'etiquetas'
        ),
        token_publico=token,
    )
    if not orden.token_vigente:
        raise Http404('Enlace de seguimiento expirado.')

    return render(request, 'workshop/seguimiento_publico.html', {
        'title': f'Seguimiento {orden.codigo_orden}',
        'orden': orden,
        'total_presupuesto': sum(
            (item.subtotal for item in orden.items_presupuesto.all()), Decimal('0')
        ),
    })


@login_required
def dashboard(request):
    rol = rol_de(request.user)
    if rol in {PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR}:
        return redirect('dashboard_admin')
    if rol == PerfilUsuario.Rol.MECANICO:
        return redirect('dashboard_tecnico')
    return redirect('dashboard_cliente')


@rol_requerido(PerfilUsuario.Rol.ADMIN, PerfilUsuario.Rol.ASESOR)
def dashboard_admin(request):
    ordenes = OrdenFalla.objects.select_related('cliente', 'mecanico_asignado')
    return render(request, 'dashboard/admin.html', {
        'title': 'Panel de administración',
        'total_ordenes': ordenes.count(),
        'ordenes_activas': ordenes.exclude(estado='ENTREGADO').count(),
        'ordenes_entregadas': ordenes.filter(estado='ENTREGADO').count(),
        'ordenes_sin_mecanico': ordenes.filter(mecanico_asignado__isnull=True).count(),
        'tecnicos': User.objects.filter(perfil__rol=PerfilUsuario.Rol.MECANICO).count(),
        'ordenes_recientes': ordenes[:8],
        'conteo_estados': [
            (dict(ESTADO_CHOICES)[codigo], ordenes.filter(estado=codigo).count())
            for codigo, _ in ESTADO_CHOICES
        ],
    })


@rol_requerido(PerfilUsuario.Rol.CLIENTE)
def dashboard_cliente(request):
    ordenes = OrdenFalla.objects.filter(cliente=request.user).prefetch_related('items_presupuesto')
    return render(request, 'dashboard/cliente.html', {
        'title': 'Mi panel',
        'ordenes': ordenes,
        'total_ordenes': ordenes.count(),
        'ordenes_activas': ordenes.exclude(estado='ENTREGADO').count(),
        'ordenes_entregadas': ordenes.filter(estado='ENTREGADO').count(),
    })


@rol_requerido(PerfilUsuario.Rol.MECANICO)
def dashboard_tecnico(request):
    ordenes = OrdenFalla.objects.filter(mecanico_asignado=request.user).select_related('cliente')
    return render(request, 'dashboard/tecnico.html', {
        'title': 'Panel del técnico',
        'ordenes': ordenes,
        'total_ordenes': ordenes.count(),
        'ordenes_activas': ordenes.exclude(estado='ENTREGADO').count(),
        'ordenes_entregadas': ordenes.filter(estado='ENTREGADO').count(),
    })
