from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import InvitacionPersonal, PerfilUsuario


class RegistroClienteForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico', required=True)
    first_name = forms.CharField(label='Nombre', max_length=150, required=False)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=False)
    telefono = forms.CharField(label='Teléfono', max_length=30, required=False)
    codigo_puesto = forms.CharField(
        label='Código de puesto',
        max_length=12,
        required=False,
        help_text='Solo para personal autorizado por el taller.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return email

    def clean_codigo_puesto(self):
        codigo = self.cleaned_data.get('codigo_puesto', '').strip().upper()
        if not codigo:
            return ''

        try:
            invitacion = InvitacionPersonal.objects.select_for_update().get(codigo=codigo)
        except InvitacionPersonal.DoesNotExist:
            raise forms.ValidationError('El código de puesto no es válido.')

        if invitacion.usado_por_id:
            raise forms.ValidationError('Este código de puesto ya fue utilizado.')
        if invitacion.expira_en <= timezone.now():
            raise forms.ValidationError('Este código de puesto ha expirado.')
        return codigo

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('codigo_puesto') and not cleaned.get('telefono', '').strip():
            self.add_error('telefono', 'Indica un teléfono de contacto para tu cuenta de cliente.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            codigo = self.cleaned_data.get('codigo_puesto', '')
            invitacion = InvitacionPersonal.objects.filter(codigo=codigo).first() if codigo else None
            if invitacion:
                perfil.rol = invitacion.rol
                perfil.telefono = self.cleaned_data.get('telefono') or invitacion.telefono
                perfil.especialidad = invitacion.especialidad
                invitacion.usado_por = user
                invitacion.save(update_fields=['usado_por'])
            else:
                perfil.rol = PerfilUsuario.Rol.CLIENTE
                perfil.telefono = self.cleaned_data['telefono'].strip()
                perfil.especialidad = ''
            perfil.save(update_fields=['rol', 'telefono', 'especialidad'])
        return user


class PerfilClienteForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico')
    first_name = forms.CharField(label='Nombre', max_length=150, required=False)
    last_name = forms.CharField(label='Apellidos', max_length=150, required=False)
    telefono = forms.CharField(label='Teléfono', max_length=30)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        initial = kwargs.pop('initial', {})
        initial.update({
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'telefono': user.perfil.telefono,
        })
        super().__init__(*args, initial=initial, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()
        if not telefono:
            raise forms.ValidationError('Indica un teléfono de contacto.')
        return telefono

    def save(self):
        self.user.email = self.cleaned_data['email']
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        self.user.save(update_fields=['email', 'first_name', 'last_name'])
        perfil = self.user.perfil
        perfil.telefono = self.cleaned_data['telefono']
        perfil.save(update_fields=['telefono'])
        return self.user


class CrearPersonalForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellidos', max_length=150)
    rol = forms.ChoiceField(
        label='Puesto',
        choices=[
            (PerfilUsuario.Rol.ASESOR, 'Asesor de servicio'),
            (PerfilUsuario.Rol.MECANICO, 'Mecánico'),
        ],
    )
    telefono = forms.CharField(label='Teléfono', max_length=30, required=False)
    especialidad = forms.CharField(label='Especialidad', max_length=100, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.rol = self.cleaned_data['rol']
            perfil.telefono = self.cleaned_data.get('telefono', '')
            perfil.especialidad = self.cleaned_data.get('especialidad', '')
            perfil.save(update_fields=['rol', 'telefono', 'especialidad'])
        return user


class InvitacionPersonalForm(forms.ModelForm):
    class Meta:
        model = InvitacionPersonal
        fields = ('rol', 'especialidad', 'telefono')

    def save(self, creado_por, commit=True):
        invitacion = super().save(commit=False)
        invitacion.creado_por = creado_por
        invitacion.expira_en = timezone.now() + timedelta(days=7)
        if commit:
            invitacion.save()
        return invitacion
