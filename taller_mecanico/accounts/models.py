from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):
    """Vincula un usuario de Django con su rol dentro del taller."""

    class Rol(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        ASESOR = 'ASESOR', 'Asesor de servicio'
        MECANICO = 'MECANICO', 'Mecánico'
        CLIENTE = 'CLIENTE', 'Cliente'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='Usuario',
    )
    rol = models.CharField('Rol', max_length=10, choices=Rol.choices, default=Rol.CLIENTE)
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    especialidad = models.CharField('Especialidad', max_length=100, blank=True)
    taller = models.CharField('Taller', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'{self.user.get_username()} ({self.get_rol_display()})'

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMIN

    @property
    def es_asesor(self):
        return self.rol == self.Rol.ASESOR

    @property
    def es_mecanico(self):
        return self.rol == self.Rol.MECANICO

    @property
    def es_cliente(self):
        return self.rol == self.Rol.CLIENTE
