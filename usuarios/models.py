from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    TIPO_DOC = [
        ('DNI', 'DNI'),
        ('CUIT', 'CUIT'),
        ('PAS', 'Pasaporte'),
        ('LE', 'Libreta de Enrolamiento'),
        ('LC', 'Libreta Cívica'),
    ]
    ROLES = [
        ('operador', 'Operador'),
        ('despachante', 'Despachante'),
        ('transportista', 'Transportista'),
        ('gerente', 'Gerente'),
        ('admin', 'Administrador'),
    ]
    nombre = models.CharField(max_length=50, null=True, blank=True)
    apellido = models.CharField(max_length=50, null=True, blank=True)

    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOC,
        default='DNI'
    )
    documento = models.CharField(max_length=20, null=True, blank=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='operador')
    telefono = models.CharField(max_length=30, null=True, blank=True)
    email=models.EmailField()
    razon_social = models.CharField(max_length=120, null=True, blank=True)
    cuit = models.CharField(max_length=20, null=True, blank=True)
    calle = models.CharField(max_length=30, null=True, blank=True)
    numero = models.IntegerField(null=True, blank=True)
    localidad = models.CharField(max_length=25,null=True, blank=True) 
    provincia = models.CharField(max_length=15,null=True, blank=True)
    pais=models.CharField(max_length=15,null=True, blank=True)
    

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
    