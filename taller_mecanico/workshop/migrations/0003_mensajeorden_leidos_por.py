import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workshop', '0002_mensajeorden'),
    ]

    operations = [
        migrations.AddField(
            model_name='mensajeorden',
            name='leidos_por',
            field=models.ManyToManyField(
                blank=True,
                related_name='mensajes_orden_leidos',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Leído por',
            ),
        ),
    ]
