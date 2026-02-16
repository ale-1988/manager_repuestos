from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


class UsuarioAdmin(UserAdmin):
    model = Usuario

    # Campos visibles en la lista del admin
    list_display = (
        'username', 'email', 'rol', 'is_staff', 'is_active'
    )

    # Campos editables en el formulario de admin
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('email',)}),
        ('Rol del sistema', {'fields': ('rol',)}),
        ('Datos adicionales', {
            'fields': (
                'telefono', 'razon_social', 'cuit',
                'calle', 'numero', 'localidad', 'provincia', 'pais'
            )
        }),
        ('Permisos', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
    )

    # Campos editables al crear un usuario desde el admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'rol',
                'nombre', 'apellido', 
                'tipo_documento', 'documento',
                'password1', 'password2',
                'is_staff', 'is_active'
            )
        }),
    )

    search_fields = ('username', 'email', 'rol','nombre', 'apellido', 'tipo_documento', 'documento')
    ordering = ('username',)


admin.site.register(Usuario, UsuarioAdmin)


