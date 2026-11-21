from django import forms
from django.contrib.auth import get_user_model
from .models import OrdenFalla


class OrdenClienteForm(forms.Form):
    vehiculo = forms.CharField(
        label='Vehículo (marca, modelo y año)',
        max_length=100,
    )
    placa = forms.CharField(
        label='Placa',
        max_length=15,
        required=False,
    )
    kilometraje_ingreso = forms.IntegerField(
        label='Kilometraje actual',
        min_value=0,
    )
    sintoma = forms.CharField(
        label='Describe el problema',
        widget=forms.Textarea,
    )


class OrdenGestionForm(forms.ModelForm):
    mecanico_asignado = forms.ModelChoiceField(
        queryset=get_user_model().objects.filter(is_staff=True).order_by('username'),
        label='Mecánico asignado',
        required=False,
        empty_label='Sin asignar',
    )

    class Meta:
        model = OrdenFalla
        fields = ('estado', 'mecanico_asignado')
        labels = {
            'estado': 'Estado del vehículo',
        }


class MensajeOrdenForm(forms.Form):
    contenido = forms.CharField(
        label='Mensaje',
        max_length=4000,
        widget=forms.Textarea(attrs={'rows': 3, 'maxlength': 4000}),
    )
