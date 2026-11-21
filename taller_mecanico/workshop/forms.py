from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from accounts.models import PerfilUsuario
from accounts.permissions import es_cliente

from .models import (
    Etiqueta,
    EvidenciaSintoma,
    ItemPresupuestoRepuestos,
    MensajeOrden,
    OrdenFalla,
    Taller,
    Vehiculo,
)


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['placa', 'marca', 'modelo', 'anio', 'motor', 'color', 'cliente']
        widgets = {
            'anio': forms.NumberInput(attrs={'min': 1900, 'max': timezone.now().year + 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = User.objects.filter(
            perfil__rol=PerfilUsuario.Rol.CLIENTE
        ).order_by('first_name', 'last_name', 'username')
        self.fields['cliente'].required = False
        self.fields['motor'].required = False
        self.fields['color'].required = False


class OrdenFallaForm(forms.ModelForm):
    placa = forms.CharField(label='Placa', max_length=20, required=False)
    marca = forms.CharField(label='Marca', max_length=50, required=False)
    modelo = forms.CharField(label='Modelo', max_length=50, required=False)
    nuevas_etiquetas = forms.CharField(
        label='Etiquetas',
        required=False,
        help_text='Escribe etiquetas separadas por comas. Ejemplo: Urgente, Garantía',
    )
    anio = forms.IntegerField(
        label='Año',
        required=False,
        widget=forms.NumberInput(attrs={'min': 1900, 'max': timezone.now().year + 1}),
    )
    motor = forms.CharField(label='Motor', max_length=50, required=False)
    nuevas_etiquetas = forms.CharField(
        label='Etiquetas nuevas',
        required=False,
        help_text='Separa varias etiquetas con comas. Ejemplo: Urgente, Garantía',
    )

    class Meta:
        model = OrdenFalla
        fields = [
            'cliente',
            'nombre_cliente_walkin',
            'telefono_cliente_walkin',
            'taller',
            'vehiculo',
            'kilometraje_ingreso',
            'etiquetas',
            'nuevas_etiquetas',
        ]
        widgets = {
            'kilometraje_ingreso': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = (
            User.objects.filter(perfil__rol=PerfilUsuario.Rol.CLIENTE)
            .order_by('first_name', 'last_name', 'username')
        )
        self.fields['cliente'].required = False
        self.fields['cliente'].help_text = (
            'Déjalo vacío si el cliente no tiene cuenta y registra su nombre abajo.'
        )
        self.fields['nombre_cliente_walkin'].help_text = (
            'Obligatorio si no seleccionas un cliente registrado.'
        )
        self.fields['etiquetas'].required = False
        self.fields['etiquetas'].queryset = Etiqueta.objects.order_by('nombre')
        self.fields['etiquetas'].widget = forms.CheckboxSelectMultiple()
        self.fields['nuevas_etiquetas'].widget.attrs.update({
            'placeholder': '#Urgente, #Garantía',
        })
        self.fields['taller'].queryset = Taller.objects.filter(activo=True)
        if not self.fields['taller'].queryset.exists():
            taller, _ = Taller.objects.get_or_create(nombre='Taller AutoDiag')
            self.fields['taller'].queryset = Taller.objects.filter(pk=taller.pk)
        self.fields['vehiculo'].queryset = Vehiculo.objects.order_by('placa')
        self.fields['vehiculo'].required = False
        self.fields['vehiculo'].help_text = (
            'Selecciona un vehículo existente o complétalo abajo para registrarlo.'
        )

        if es_cliente(user):
            self.instance.cliente = user
            for campo in ('cliente', 'nombre_cliente_walkin', 'telefono_cliente_walkin'):
                self.fields.pop(campo, None)

    def clean(self):
        cleaned_data = super().clean()
        if es_cliente(self.user):
            cleaned_data['cliente'] = self.user

        vehiculo = cleaned_data.get('vehiculo')
        if not vehiculo:
            requeridos = ('placa', 'marca', 'modelo', 'anio')
            faltantes = [campo for campo in requeridos if not cleaned_data.get(campo)]
            if faltantes:
                raise forms.ValidationError(
                    'Selecciona un vehículo o completa placa, marca, modelo y año.'
                )
            placa = cleaned_data['placa'].strip().upper()
            if Vehiculo.objects.filter(placa__iexact=placa).exists():
                self.add_error('placa', 'Ya existe un vehículo con esta placa.')
        return cleaned_data

    def save(self, commit=True):
        if not self.cleaned_data.get('vehiculo'):
            self.instance.vehiculo = Vehiculo.objects.create(
                placa=self.cleaned_data['placa'].strip().upper(),
                marca=self.cleaned_data['marca'].strip(),
                modelo=self.cleaned_data['modelo'].strip(),
                anio=self.cleaned_data['anio'],
                motor=self.cleaned_data.get('motor', '').strip(),
                cliente=self.cleaned_data.get('cliente') if not es_cliente(self.user) else self.user,
            )
        orden = super().save(commit=commit)
        return orden


class EditarOrdenForm(forms.ModelForm):
    placa = forms.CharField(label='Placa', max_length=20)
    marca = forms.CharField(label='Marca', max_length=50)
    modelo = forms.CharField(label='Modelo', max_length=50)
    anio = forms.IntegerField(
        label='Año',
        widget=forms.NumberInput(attrs={'min': 1900, 'max': timezone.now().year + 1}),
    )
    motor = forms.CharField(label='Motor', max_length=50, required=False)
    color = forms.CharField(label='Color', max_length=30, required=False)
    nuevas_etiquetas = forms.CharField(
        label='Etiquetas nuevas',
        required=False,
        help_text='Separa varias etiquetas con comas. Ejemplo: Urgente, Garantía',
    )

    class Meta:
        model = OrdenFalla
        fields = [
            'cliente',
            'nombre_cliente_walkin',
            'telefono_cliente_walkin',
            'taller',
            'mecanico_asignado',
            'kilometraje_ingreso',
            'etiquetas',
            'nuevas_etiquetas',
        ]
        widgets = {
            'kilometraje_ingreso': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = User.objects.filter(
            perfil__rol=PerfilUsuario.Rol.CLIENTE
        ).order_by('first_name', 'last_name', 'username')
        self.fields['cliente'].required = False
        self.fields['nombre_cliente_walkin'].required = False
        self.fields['telefono_cliente_walkin'].required = False
        self.fields['etiquetas'].required = False
        self.fields['etiquetas'].queryset = Etiqueta.objects.order_by('nombre')
        self.fields['taller'].queryset = Taller.objects.filter(activo=True)
        self.fields['mecanico_asignado'].queryset = User.objects.filter(
            perfil__rol=PerfilUsuario.Rol.MECANICO
        ).order_by('first_name', 'last_name', 'username')
        self.fields['mecanico_asignado'].required = False

        vehiculo = getattr(self.instance, 'vehiculo', None)
        if vehiculo:
            for campo, valor in (
                ('placa', vehiculo.placa),
                ('marca', vehiculo.marca),
                ('modelo', vehiculo.modelo),
                ('anio', vehiculo.anio),
                ('motor', vehiculo.motor),
                ('color', vehiculo.color),
            ):
                self.initial.setdefault(campo, valor)

    def clean(self):
        cleaned_data = super().clean()
        placa = (cleaned_data.get('placa') or '').strip().upper()
        cleaned_data['placa'] = placa
        if placa:
            repetida = Vehiculo.objects.filter(placa__iexact=placa).exclude(
                pk=getattr(self.instance.vehiculo, 'pk', None)
            )
            if repetida.exists():
                self.add_error('placa', 'Ya existe otro vehículo con esta placa.')
        if not cleaned_data.get('cliente') and not (
            cleaned_data.get('nombre_cliente_walkin') or ''
        ).strip():
            self.add_error(
                'nombre_cliente_walkin',
                'Selecciona un cliente registrado o indica el nombre del cliente walk-in.',
            )
        return cleaned_data

    def save(self, commit=True):
        orden = super().save(commit=commit)
        vehiculo = orden.vehiculo
        vehiculo.placa = self.cleaned_data['placa']
        vehiculo.marca = self.cleaned_data['marca']
        vehiculo.modelo = self.cleaned_data['modelo']
        vehiculo.anio = self.cleaned_data['anio']
        vehiculo.motor = self.cleaned_data.get('motor', '')
        vehiculo.color = self.cleaned_data.get('color', '')
        vehiculo.cliente = orden.cliente
        if commit:
            vehiculo.save()

        nuevas_etiquetas = self.cleaned_data.get('nuevas_etiquetas', '')
        nombres = [
            nombre.strip().lstrip('#')
            for nombre in nuevas_etiquetas.split(',')
            if nombre.strip()
        ]
        for nombre in dict.fromkeys(nombres):
            etiqueta, _ = Etiqueta.objects.get_or_create(
                nombre=f'#{nombre}',
                defaults={'color': '#6C757D'},
            )
            orden.etiquetas.add(etiqueta)
        return orden


class ClienteRapidoForm(forms.Form):
    nombre_completo = forms.CharField(label='Nombre completo', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    telefono = forms.CharField(label='Teléfono', max_length=30)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este usuario.')
        return email

    def save(self):
        email = self.cleaned_data['email']
        nombre = self.cleaned_data['nombre_completo'].strip()
        partes = nombre.split(' ', 1)
        user = User(
            username=email,
            email=email,
            first_name=partes[0],
            last_name=partes[1] if len(partes) > 1 else '',
        )
        user.set_unusable_password()
        user.save()

        perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
        perfil.rol = PerfilUsuario.Rol.CLIENTE
        perfil.telefono = self.cleaned_data.get('telefono', '')
        perfil.save()
        return user


class EvidenciaSintomaForm(forms.ModelForm):
    class Meta:
        model = EvidenciaSintoma
        fields = ['archivo_audio', 'imagen', 'narrativa_cliente', 'nivel_riesgo']
        widgets = {
            'narrativa_cliente': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe el ruido, la vibración, la luz o el comportamiento del vehículo.',
            }),
            'archivo_audio': forms.ClearableFileInput(attrs={
                'accept': 'audio/*',
                'capture': 'microphone',
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'accept': 'image/*',
                'capture': 'environment',
            }),
        }


class MensajeOrdenForm(forms.ModelForm):
    class Meta:
        model = MensajeOrden
        fields = ['contenido']
        labels = {'contenido': 'Mensaje'}
        widgets = {
            'contenido': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Escribe un mensaje sobre este ticket...',
            }),
        }


class ItemPresupuestoForm(forms.ModelForm):
    class Meta:
        model = ItemPresupuestoRepuestos
        fields = ['tipo', 'descripcion', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1}),
            'precio_unitario': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }


class CambioEstadoForm(forms.Form):
    estado = forms.ChoiceField(label='Nuevo estado')

    def __init__(self, orden, *args, **kwargs):
        self.orden = orden
        super().__init__(*args, **kwargs)
        self.fields['estado'].choices = orden.estados_siguientes or [('', 'Sin transiciones disponibles')]


class AsignarMecanicoForm(forms.ModelForm):
    class Meta:
        model = OrdenFalla
        fields = ['mecanico_asignado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mecanico_asignado'].queryset = (
            User.objects.filter(perfil__rol=PerfilUsuario.Rol.MECANICO)
            .order_by('first_name', 'last_name', 'username')
        )
        self.fields['mecanico_asignado'].required = False
