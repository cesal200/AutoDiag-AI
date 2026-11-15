from django.db import migrations


def backfill_perfiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    PerfilUsuario = apps.get_model('accounts', 'PerfilUsuario')

    for user in User.objects.all():
        if user.is_superuser:
            rol = 'ADMIN'
        elif user.is_staff:
            rol = 'ASESOR'
        else:
            rol = 'CLIENTE'
        PerfilUsuario.objects.get_or_create(user=user, defaults={'rol': rol})


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(backfill_perfiles, reverse_noop),
    ]
