from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegistroClienteForm


def registro(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegistroClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Cuenta creada. Ya puedes registrar tu orden.')
        return redirect('dashboard')

    return render(request, 'accounts/registro.html', {'form': form})
