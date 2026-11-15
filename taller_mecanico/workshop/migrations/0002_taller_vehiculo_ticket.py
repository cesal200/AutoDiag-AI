import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def migrar_talleres_y_vehiculos(apps, schema_editor):
    OrdenFalla = apps.get_model('workshop', 'OrdenFalla')
    Taller = apps.get_model('workshop', 'Taller')
    Vehiculo = apps.get_model('workshop', 'Vehiculo')
    anio = timezone.localdate().year

    for orden in OrdenFalla.objects.all().iterator():
        nombre_taller = (orden.taller_legacy or 'Taller AutoDiag').strip()
        taller, _ = Taller.objects.get_or_create(nombre=nombre_taller)

        descripcion = (orden.vehiculo_legacy or 'Vehículo sin datos').strip()
        partes = descripcion.split(' ', 1)
        marca = partes[0][:50] or 'Sin marca'
        modelo = (partes[1] if len(partes) > 1 else 'Sin modelo')[:50]
        placa = f'LEG-{orden.id:06d}'
        vehiculo, _ = Vehiculo.objects.get_or_create(
            placa=placa,
            defaults={
                'marca': marca,
                'modelo': modelo,
                'anio': anio,
                'cliente_id': orden.cliente_id,
            },
        )

        orden.taller_id = taller.id
        orden.vehiculo_id = vehiculo.id
        orden.ticket = f'TKT-{anio}-{orden.id:03d}'
        orden.save(update_fields=['taller', 'vehiculo', 'ticket'])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workshop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Taller',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
                ('direccion', models.CharField(blank=True, max_length=200, verbose_name='Dirección')),
                ('telefono', models.CharField(blank=True, max_length=30, verbose_name='Teléfono')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Taller',
                'verbose_name_plural': 'Talleres',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Vehiculo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('placa', models.CharField(max_length=20, unique=True, verbose_name='Placa')),
                ('marca', models.CharField(max_length=50, verbose_name='Marca')),
                ('modelo', models.CharField(max_length=50, verbose_name='Modelo')),
                ('anio', models.PositiveIntegerField(verbose_name='Año')),
                ('motor', models.CharField(blank=True, max_length=50, verbose_name='Motor')),
                ('color', models.CharField(blank=True, max_length=30, verbose_name='Color')),
                ('creado_en', models.DateTimeField(auto_now_add=True, verbose_name='Creado En')),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vehiculos', to=settings.AUTH_USER_MODEL, verbose_name='Cliente')),
            ],
            options={
                'verbose_name': 'Vehículo',
                'verbose_name_plural': 'Vehículos',
                'ordering': ['placa'],
            },
        ),
        migrations.RenameField(
            model_name='ordenfalla',
            old_name='taller',
            new_name='taller_legacy',
        ),
        migrations.RenameField(
            model_name='ordenfalla',
            old_name='vehiculo',
            new_name='vehiculo_legacy',
        ),
        migrations.AddField(
            model_name='ordenfalla',
            name='ticket',
            field=models.CharField(default='', editable=False, max_length=20, verbose_name='Ticket'),
        ),
        migrations.AddField(
            model_name='ordenfalla',
            name='taller',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ordenes', to='workshop.taller', verbose_name='Taller'),
        ),
        migrations.AddField(
            model_name='ordenfalla',
            name='vehiculo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ordenes', to='workshop.vehiculo', verbose_name='Vehículo'),
        ),
        migrations.RunPython(migrar_talleres_y_vehiculos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='ordenfalla',
            name='taller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ordenes', to='workshop.taller', verbose_name='Taller'),
        ),
        migrations.AlterField(
            model_name='ordenfalla',
            name='vehiculo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ordenes', to='workshop.vehiculo', verbose_name='Vehículo'),
        ),
        migrations.RemoveField(
            model_name='ordenfalla',
            name='taller_legacy',
        ),
        migrations.RemoveField(
            model_name='ordenfalla',
            name='vehiculo_legacy',
        ),
        migrations.AlterField(
            model_name='ordenfalla',
            name='ticket',
            field=models.CharField(default='', editable=False, max_length=20, unique=True, verbose_name='Ticket'),
        ),
        migrations.AlterField(
            model_name='ordenfalla',
            name='kilometraje_ingreso',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name='Kilometraje Ingreso'),
        ),
        migrations.AlterField(
            model_name='itempresupuestorepuestos',
            name='cantidad',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Cantidad'),
        ),
        migrations.AlterField(
            model_name='itempresupuestorepuestos',
            name='precio_unitario',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Precio Unitario'),
        ),
    ]
