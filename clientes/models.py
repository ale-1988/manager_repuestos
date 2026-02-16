from django.db import models

class Clientes(models.Model):
    id = models.IntegerField(primary_key=True, db_column='id')
    nombre = models.CharField(max_length=100, db_column='nombre')
    cuit = models.CharField(max_length=15, db_column='cuit')
    domicilio = models.CharField(max_length=50, db_column='domicilio')
    ciudad = models.CharField(max_length=40, db_column='ciudad')
    cod_postal = models.CharField(max_length=10, db_column='cod_postal')
    provincia = models.CharField(max_length=20, db_column='provincia')
    pais = models.CharField(max_length=20, db_column='pais')
    telefono = models.CharField(max_length=40, db_column='telefono', null=True, blank=True)
    email = models.CharField(max_length=50, db_column='email', null=True, blank=True)

    class Meta:
        managed = False               # NO modificar la tabla legacy
        db_table = 'datos'            # nombre exacto de la tabla

    def __str__(self):
        return f"{self.id} - {self.nombre}"



