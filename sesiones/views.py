from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
# from django.urls import reverse

@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect("sesiones:inicio")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            next_url = request.GET.get("next")
            if next_url:
                return redirect(next_url)
            else:
                # return redirect("sesiones:inicio")
                return redirect("/pedidos/listar/")
            return redirect(next_url)
        else:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "sesiones/login.html")


def logout_view(request):
    logout(request)
    return redirect("sesiones:login")


def inicio(request):
    return render(request, "inicio.html")