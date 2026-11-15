import json
import os
import urllib.request

from django.core.mail import get_connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Comprueba la configuración de Telegram y SMTP para distribuir reportes.'

    def handle(self, *args, **options):
        self._probar_telegram()
        self._probar_email()

    def _probar_telegram(self):
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
        if not token:
            self.stdout.write(self.style.WARNING(
                'Telegram: TELEGRAM_BOT_TOKEN no configurado. Se usará solo la descarga local.'
            ))
            return
        try:
            with urllib.request.urlopen(
                f'https://api.telegram.org/bot{token}/getMe', timeout=15
            ) as response:
                data = json.loads(response.read().decode('utf-8'))
            if data.get('ok'):
                self.stdout.write(self.style.SUCCESS(
                    f"Telegram: bot @{data['result'].get('username', 'desconocido')} operativo."
                ))
            else:
                self.stdout.write(self.style.ERROR(f"Telegram: {data}"))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Telegram: no se pudo conectar ({exc}).'))

    def _probar_email(self):
        connection = get_connection()
        if connection.__class__.__name__ == 'ConsoleEmailBackend':
            self.stdout.write(self.style.WARNING(
                'Email: backend de consola activo. Configure EMAIL_BACKEND y credenciales SMTP.'
            ))
            return
        try:
            connection.open()
            connection.close()
            self.stdout.write(self.style.SUCCESS('Email: conexión SMTP establecida.'))
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f'Email: no se pudo conectar ({exc}).'))
