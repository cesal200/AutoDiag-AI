from django import forms

from .models import ConfiguracionDistribucion, ConfiguracionRemitente


class ConfiguracionDistribucionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionDistribucion
        fields = ['metodo', 'chat_telegram_id', 'email_destino', 'telefono_whatsapp']
        labels = {
            'email_destino': 'Correo del cliente',
            'telefono_whatsapp': 'Teléfono WhatsApp del cliente (opcional)',
        }
        widgets = {
            'chat_telegram_id': forms.TextInput(attrs={'placeholder': 'Ej. 123456789'}),
            'email_destino': forms.EmailInput(attrs={'placeholder': 'cliente@ejemplo.com'}),
            'telefono_whatsapp': forms.TextInput(attrs={'placeholder': 'Teléfono del cliente'}),
        }

    def clean(self):
        cleaned = super().clean()
        metodo = cleaned.get('metodo')
        if metodo in {'TELEGRAM', 'AMBOS'} and not cleaned.get('chat_telegram_id'):
            self.add_error('chat_telegram_id', 'Indica el chat de Telegram para este método.')
        if metodo in {'EMAIL', 'AMBOS', 'WHATSAPP_EMAIL'} and not cleaned.get('email_destino'):
            self.add_error('email_destino', 'Indica el correo de destino para este método.')
        return cleaned


class ConfiguracionRemitenteForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionRemitente
        fields = ['telefono_whatsapp', 'email_remitente']
        widgets = {
            'telefono_whatsapp': forms.TextInput(attrs={
                'placeholder': 'Ej. +18095550101',
            }),
            'email_remitente': forms.EmailInput(attrs={
                'placeholder': 'reportes@taller.com',
            }),
        }
