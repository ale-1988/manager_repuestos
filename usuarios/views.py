from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Usuario
from .forms import UsuarioCreateForm, UsuarioUpdateForm


# ============================================
# Decorador para restringir por rol
# ============================================
def requiere_rol(*roles_permitidos):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.rol not in roles_permitidos:
                return HttpResponseForbidden("No está autorizado para acceder a este módulo.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ============================================
# Lista usuarios
# ============================================
@login_required
@requiere_rol('admin', 'gerente')
def listar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'usuarios/listar.html', {'usuarios': usuarios})


# ============================================
# Crea usuario
# ============================================
@login_required
@requiere_rol('admin', 'gerente')
def nuevo_usuario(request):
    if request.method == "POST":
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:listar')
    else:
        form = UsuarioCreateForm()

    return render(request, 'usuarios/form.html', {
        'form': form,
        'titulo': 'Crear usuario',
        'accion': 'Crear'
    })


# ============================================
# Edita usuario
# ============================================
@login_required
@requiere_rol('admin', 'gerente')
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, pk=id)

    if request.method == "POST":
        form = UsuarioUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('usuarios:listar')
    else:
        form = UsuarioUpdateForm(instance=usuario)

    return render(request, 'usuarios/form.html', {
        'form': form,
        'titulo': 'Editar usuario',
        'accion': 'Guardar cambios'
    })


# ============================================
# Elimina usuario
# ============================================
@login_required
@requiere_rol('admin', 'gerente')
def eliminar_usuario(request, id):
    usuario = get_object_or_404(Usuario, pk=id)

    if request.method == "POST":
        usuario.delete()
        return redirect('usuarios:listar')

    return render(request, 'usuarios/eliminar.html', {
        'usuario': usuario
    })


