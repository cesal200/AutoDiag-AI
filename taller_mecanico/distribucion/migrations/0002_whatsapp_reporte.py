from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('distribucion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuraciondistribucion',
            name='metodo',
            field=models.CharField(
                choices=[
                    ('TELEGRAM', 'Telegram'),
                    ('EMAIL', 'Email'),
                    ('WHATSAPP', 'WhatsApp Web'),
                    ('WHATSAPP_EMAIL', 'WhatsApp y Email'),
                    ('AMBOS', 'Ambos'),
                    ('NINGUNO', 'Ninguno'),
                ],
                default='TELEGRAM',
                max_length=20,
                verbose_name='Método de Distribución',
            ),
        ),
        migrations.AddField(
            model_name='configuraciondistribucion',
            name='telefono_whatsapp',
            field=models.CharField(
                blank=True,
                max_length=30,
                null=True,
                verbose_name='Teléfono WhatsApp',
            ),
        ),
    ]
