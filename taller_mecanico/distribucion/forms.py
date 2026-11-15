from django import forms

from .models import ConfiguracionDistribucion


class ConfiguracionDistribucionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionDistribucion
        fields = ['metodo', 'chat_telegram_id', 'email_destino']
        widgets = {
            'chat_telegram_id': forms.TextInput(attrs={'placeholder': 'Ej. 123456789'}),
            'email_destino': forms.EmailInput(attrs={'placeholder': 'cliente@ejemplo.com'}),
        }

    def clean(self):
        cleaned = super().clean()
        metodo = cleaned.get('metodo')
        if metodo in {'TELEGRAM', 'AMBOS'} and not cleaned.get('chat_telegram_id'):
            self.add_error('chat_telegram_id', 'Indica el chat de Telegram para este método.')
        if metodo in {'EMAIL', 'AMBOS'} and not cleaned.get('email_destino'):
            self.add_error('email_destino', 'Indica el correo de destino para este método.')
        return cleaned
