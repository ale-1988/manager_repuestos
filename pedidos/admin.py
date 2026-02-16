from django.contrib import admin

# Register your models here.
class PedidoItemInline(admin.TabularInline):
    def has_add_permission(self, request, obj):
        return obj is not None and obj.estado == 'CREADO'

    def has_change_permission(self, request, obj=None):
        return obj is not None and obj.estado == 'CREADO'

    def has_delete_permission(self, request, obj=None):
        return obj is not None and obj.estado == 'CREADO'
