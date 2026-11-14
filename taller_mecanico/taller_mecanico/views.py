from django.shortcuts import render


def home(request):
    return render(request, 'home.html', {
        'title': 'AutoDiag AI',
        'summary': 'Panel principal del taller mecánico con prediagnóstico inteligente.',
    })
