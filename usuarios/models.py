from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    ROLES = [
        ('cliente', 'Cliente'),
        ('operador', 'Operador'),
        ('despachante', 'Despachante'),
        ('transportista', 'Transportista'),
        ('gerente', 'Gerente'),
        ('admin', 'Administrador'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=30, blank=True)
    email=models.EmailField()
    razon_social = models.CharField(max_length=120, blank=True)
    cuit = models.CharField(max_length=20, blank=True)
    calle = models.CharField(max_length=30, blank=True)
    numero = models.IntegerField()
    localidad = models.CharField(max_length=25) 
    provincia = models.CharField(max_length=15)
    pais=models.CharField(max_length=15)
    

    def __str__(self):
        return self.username
    
# ==============================
# Usuario especializado
# ==============================
class Transportista(Usuario):
    """Usuario especializado como transportista."""
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Transportista"
        verbose_name_plural = "Transportistas"

    def __str__(self):
        return f"{self.username} (Transportista)"
    