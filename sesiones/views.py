from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect

# ===========================
#     Vista de login
# ===========================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Si venía de un login_required, redirige a ?next=/lo-que-sea
            next_url = request.GET.get("next", "/")
            return redirect(next_url)
        else:
            messages.error(request, "Usuario o contraseña inválidos")

    return render(request, "login.html")   # Debe existir este template


# ===========================
#     Vista de logout
# ===========================
@csrf_protect
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("/login/")
    else:
        #Si entran por GET, redirigimos a inicio o login
        return redirect("/")


# ===========================
#     Vista de inicio# ===========================
@csrf_protect
@login_required
def inicio(request):
    return render(request, "inicio.html")
