import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_backfill_perfiles'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitacionPersonal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(editable=False, max_length=12, unique=True, verbose_name='Código')),
                ('rol', models.CharField(choices=[('ASESOR', 'Asesor de servicio'), ('MECANICO', 'Mecánico')], max_length=10, verbose_name='Puesto')),
                ('especialidad', models.CharField(blank=True, max_length=100, verbose_name='Especialidad')),
                ('telefono', models.CharField(blank=True, max_length=30, verbose_name='Teléfono')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('expira_en', models.DateTimeField(verbose_name='Expira')),
                ('creado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='invitaciones_emitidas', to=settings.AUTH_USER_MODEL)),
                ('usado_por', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitacion_personal', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Invitación de personal',
                'verbose_name_plural': 'Invitaciones de personal',
                'ordering': ['-creado_en'],
            },
        ),
    ]
