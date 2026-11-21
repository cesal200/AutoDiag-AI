from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect, render

from accounts.decorators import rol_requerido
from accounts.models import InvitacionPersonal, PerfilUsuario

from .forms import (
    CrearPersonalForm,
    InvitacionPersonalForm,
    PerfilClienteForm,
    RegistroClienteForm,
)


def registro(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        if user.perfil.rol == PerfilUsuario.Rol.CLIENTE:
            messages.success(request, 'Cuenta creada. Ya puedes registrar tu orden.')
        else:
            messages.success(
                request,
                f'Cuenta creada con el puesto de {user.perfil.get_rol_display()}.',
            )
        return redirect('dashboard')

    return render(request, 'accounts/registro.html', {'form': form})


@rol_requerido(PerfilUsuario.Rol.CLIENTE)
def perfil_cliente(request):
    form = PerfilClienteForm(
        request.POST or None,
        user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tus datos de contacto se actualizaron.')
        return redirect('perfil_cliente')

    return render(request, 'accounts/perfil_cliente.html', {
        'form': form,
    })


@rol_requerido(PerfilUsuario.Rol.ADMIN)
def gestionar_personal(request):
    crear_form = CrearPersonalForm(request.POST if 'crear_personal' in request.POST else None)
    invitacion_form = InvitacionPersonalForm(
        request.POST if 'crear_invitacion' in request.POST else None
    )

    if request.method == 'POST' and 'crear_personal' in request.POST:
        if crear_form.is_valid():
            user = crear_form.save()
            messages.success(
                request,
                f'Usuario {user.username} creado como {user.perfil.get_rol_display()}.',
            )
            return redirect('gestionar_personal')
        invitacion_form = InvitacionPersonalForm()
    elif request.method == 'POST' and 'crear_invitacion' in request.POST:
        if invitacion_form.is_valid():
            invitacion = invitacion_form.save(creado_por=request.user)
            messages.success(
                request,
                f'Código de puesto creado: {invitacion.codigo}',
            )
            return redirect('gestionar_personal')
        crear_form = CrearPersonalForm()

    invitaciones = InvitacionPersonal.objects.select_related(
        'creado_por', 'usado_por'
    ).all()
    personal = PerfilUsuario.objects.select_related('user').exclude(
        rol=PerfilUsuario.Rol.CLIENTE
    ).order_by('rol', 'user__first_name', 'user__username')

    return render(request, 'accounts/gestionar_personal.html', {
        'crear_form': crear_form,
        'invitacion_form': invitacion_form,
        'invitaciones': invitaciones,
        'personal': personal,
    })


@rol_requerido(PerfilUsuario.Rol.ADMIN)
def gestionar_usuarios(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        accion = request.POST.get('accion')

        try:
            usuario = User.objects.select_related('perfil').get(pk=usuario_id)
        except User.DoesNotExist:
            messages.error(request, 'El usuario seleccionado ya no existe.')
            return redirect('gestionar_usuarios')

        if accion == 'actualizar':
            rol = request.POST.get('rol')
            roles_validos = {choice[0] for choice in PerfilUsuario.Rol.choices}
            if rol not in roles_validos:
                messages.error(request, 'El puesto seleccionado no es válido.')
            else:
                perfil = usuario.perfil
                perfil.rol = rol
                perfil.telefono = request.POST.get('telefono', '').strip()
                perfil.especialidad = request.POST.get('especialidad', '').strip()
                perfil.save(update_fields=['rol', 'telefono', 'especialidad'])
                messages.success(request, f'Usuario {usuario.username} actualizado.')

        elif accion == 'eliminar':
            if usuario.pk == request.user.pk:
                messages.error(request, 'No puedes eliminar tu propia cuenta mientras estés conectado.')
            elif usuario.is_superuser:
                messages.error(request, 'No puedes eliminar otra cuenta administradora del sistema.')
            else:
                nombre = usuario.username
                usuario.delete()
                messages.success(request, f'Usuario {nombre} eliminado del sistema.')
        else:
            raise PermissionDenied

        return redirect('gestionar_usuarios')

    busqueda = request.GET.get('q', '').strip()
    rol_filtro = request.GET.get('rol', '').strip()
    usuarios = User.objects.select_related('perfil').order_by(
        'perfil__rol', 'first_name', 'last_name', 'username'
    )

    if busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=busqueda)
            | Q(email__icontains=busqueda)
            | Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
        )
    if rol_filtro in dict(PerfilUsuario.Rol.choices):
        usuarios = usuarios.filter(perfil__rol=rol_filtro)

    return render(request, 'accounts/gestionar_usuarios.html', {
        'usuarios': usuarios,
        'roles': PerfilUsuario.Rol.choices,
        'busqueda': busqueda,
        'rol_filtro': rol_filtro,
    })
