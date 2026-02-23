from django.shortcuts import redirect

def custom_404(request, exception):
    if request.user.is_authenticated:
        return redirect("pedidos:listar")
    return redirect("sesiones:login")