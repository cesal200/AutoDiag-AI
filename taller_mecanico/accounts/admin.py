from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import InvitacionPersonal, PerfilUsuario


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


@admin.register(InvitacionPersonal)
class InvitacionPersonalAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'rol', 'especialidad', 'creado_por', 'usado_por', 'expira_en', 'vigente')
    list_filter = ('rol',)
    search_fields = ('codigo', 'especialidad', 'telefono')
    readonly_fields = ('codigo', 'creado_por', 'usado_por', 'creado_en')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
            if not obj.expira_en:
                from django.utils import timezone
                from datetime import timedelta
                obj.expira_en = timezone.now() + timedelta(days=7)
        super().save_model(request, obj, form, change)
