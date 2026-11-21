from django.conf import settings
from django.db import models
from django.utils import timezone
import secrets
import string


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


class InvitacionPersonal(models.Model):
    """Código emitido por el taller para registrar personal con un puesto definido."""

    codigo = models.CharField('Código', max_length=12, unique=True, editable=False)
    rol = models.CharField(
        'Puesto',
        max_length=10,
        choices=[
            (PerfilUsuario.Rol.ASESOR, 'Asesor de servicio'),
            (PerfilUsuario.Rol.MECANICO, 'Mecánico'),
        ],
    )
    especialidad = models.CharField('Especialidad', max_length=100, blank=True)
    telefono = models.CharField('Teléfono', max_length=30, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='invitaciones_emitidas',
    )
    usado_por = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitacion_personal',
    )
    expira_en = models.DateTimeField('Expira')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Invitación de personal'
        verbose_name_plural = 'Invitaciones de personal'
        ordering = ['-creado_en']

    def save(self, *args, **kwargs):
        if not self.codigo:
            caracteres = string.ascii_uppercase + string.digits
            while True:
                codigo = ''.join(secrets.choice(caracteres) for _ in range(8))
                if not InvitacionPersonal.objects.filter(codigo=codigo).exists():
                    self.codigo = codigo
                    break
        super().save(*args, **kwargs)

    @property
    def vigente(self):
        return self.usado_por_id is None and self.expira_en > timezone.now()

    def __str__(self):
        return f'{self.codigo} - {self.get_rol_display()}'
