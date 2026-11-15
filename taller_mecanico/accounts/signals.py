from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PerfilUsuario


@receiver(post_save, sender=User)
def crear_o_actualizar_perfil(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    if created:
        rol = PerfilUsuario.Rol.ADMIN if instance.is_superuser else PerfilUsuario.Rol.CLIENTE
        PerfilUsuario.objects.get_or_create(user=instance, defaults={'rol': rol})
        return

    perfil = PerfilUsuario.objects.filter(user=instance).first()
    if perfil and instance.is_superuser and perfil.rol != PerfilUsuario.Rol.ADMIN:
        perfil.rol = PerfilUsuario.Rol.ADMIN
        perfil.save(update_fields=['rol'])
