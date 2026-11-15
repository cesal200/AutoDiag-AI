from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import PerfilUsuario


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    extra = 0
    verbose_name = 'Perfil y rol'
    verbose_name_plural = 'Perfil y rol'


class UserAdmin(BaseUserAdmin):
    inlines = [PerfilUsuarioInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'telefono', 'especialidad', 'taller')
    list_filter = ('rol',)
    search_fields = ('user__username', 'user__email', 'telefono')
