from django.db import models

class Repuesto(models.Model):
    id = models.IntegerField(unique=True)
    descripcion = models.CharField(max_length=200)
    imagen = models.ImageField(upload_to="repuestos/images", blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"