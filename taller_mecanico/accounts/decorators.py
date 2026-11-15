from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from .permissions import rol_de


def rol_requerido(*roles):
    """Permite la vista solo a los roles indicados (superuser siempre pasa)."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_superuser and rol_de(request.user) not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


class RolRequeridoMixin(LoginRequiredMixin):
    roles_permitidos = ()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.user.is_superuser and rol_de(request.user) not in self.roles_permitidos:
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
