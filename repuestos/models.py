from django.db import models


# ===============================
#   TABLA LEGACY: grupos
# ===============================

class Grupos(models.Model):
    GRUPO = models.CharField(
        max_length=50,
        db_column='GRUPO',
        null=True,
        blank=True
    )
    id_grup = models.AutoField(
        primary_key=True,
        db_column='id_grup'
    )
    notas = models.TextField(
        db_column='notas',
        null=True,
        blank=True
    )
    grupo_conjuntos = models.IntegerField(db_column='grupo_conjuntos')
    grupo_embalaje = models.IntegerField(db_column='grupo_embalaje')
    relevanciaMadre = models.IntegerField(db_column='relevanciaMadre')

    class Meta:
        managed = False
        db_table = 'grupos'

    def __str__(self):
        return f"{self.id_grup} - {self.GRUPO}"


# ===============================
#   TABLA LEGACY: equipos
# ===============================

class Equipos(models.Model):
    equipo = models.CharField(
        max_length=150,
        db_column='equipo',
        null=True,
        blank=True
    )
    id_equi = models.AutoField(
        primary_key=True,
        db_column='id_equi'
    )
    notas = models.TextField(db_column='notas')
    id_grup = models.IntegerField(
        db_column='id_grup',
        null=True,
        blank=True
    )
    obsoleto = models.IntegerField(
        db_column='obsoleto',
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = 'equipos'

    def __str__(self):
        return f"{self.id_equi} - {self.equipo}"


# ===============================
#   TABLA LEGACY: material
# ===============================

class Material(models.Model):
    unidad = models.CharField(max_length=25, db_column='unidad')
    fecha_precio = models.IntegerField(db_column='fecha_precio')
    comprar = models.IntegerField(db_column='comprar')

    # FK hacia grupos
    id_grup = models.ForeignKey(
        Grupos,
        on_delete=models.DO_NOTHING,
        db_column='id_grup'
    )

    stock = models.DecimalField(max_digits=11, decimal_places=3, db_column='stock')
    precio = models.DecimalField(max_digits=11, decimal_places=3, db_column='precio')
    id_mate = models.AutoField(primary_key=True, db_column='id_mate')
    critico = models.IntegerField(db_column='critico')
    pila = models.IntegerField(db_column='pila')
    valor = models.CharField(max_length=50, db_column='valor')
    lugar = models.CharField(max_length=50, db_column='lugar')
    origen = models.SmallIntegerField(db_column='origen')
    historia = models.TextField(db_column='historia')
    div_precio = models.IntegerField(db_column='div_precio')
    descripcio = models.TextField(db_column='descripcio')
    stockNC = models.DecimalField(max_digits=11, decimal_places=3, db_column='stockNC')
    stockProd = models.DecimalField(max_digits=11, decimal_places=3, db_column='stockProd')
    grafLink = models.CharField(max_length=250, db_column='grafLink')
    cod_tipo_producto = models.IntegerField(db_column='cod_tipo_producto')
    cod_M2 = models.IntegerField(db_column='cod_M2')

    class Meta:
        managed = False
        db_table = 'material'

    def __str__(self):
        return f"{self.id_mate} - {self.valor}"

    @property
    def extra(self):
        return getattr(self, "material2", None)
    
    @property
    def grupo_nombre(self):
        return self.id_grup.GRUPO if self.id_grup else None

    # # ========= MÉTODO PEDIDO =========
    # def get_equipo_asociado(self):
    #     """
    #     Reproduce el SELECT legacy que relaciona:
    #     material → material2 → equipo → grupo
    #     """
    #     try:
    #         m2 = self.material2
    #         equipo = m2.conjunto
    #         grupo = self.id_grup

    #         return {
    #             "valor": self.valor,
    #             "material2_conjunto": m2.conjunto_id,
    #             "grupo": grupo.GRUPO,
    #             "grupo_notas": grupo.notas,
    #             "id_equi": equipo.id_equi,
    #             "equipo_nombre": equipo.equipo,
    #             "equipo_notas": equipo.notas,
    #             "equipo_id_grup": equipo.id_grup,
    #             "equipo_obsoleto": equipo.obsoleto,
    #         }

    #     except Exception as e:
    #         return {"error": str(e)}


# ===============================
#   TABLA LEGACY: material2
# ===============================

class Material2(models.Model):
    material = models.OneToOneField(
        Material,
        on_delete=models.DO_NOTHING,
        db_column='id_mate',
        primary_key=True
    )
    moneda = models.IntegerField(db_column='moneda')
    consumo = models.DecimalField(max_digits=11, decimal_places=3, db_column='consumo')
    fecha_consumo = models.IntegerField(db_column='fecha_consumo')
    requerimientos = models.TextField(db_column='requerimientos')
    req_especial = models.IntegerField(db_column='req_especial')

    # FK hacia equipos (campo "conjunto")
    conjunto = models.ForeignKey(
        Equipos,
        on_delete=models.DO_NOTHING,
        db_column='conjunto'
    )

    obsoleto = models.IntegerField(db_column='obsoleto')
    discontinuado = models.BooleanField(db_column='discontinuado')
    discont_razon = models.TextField(db_column='discont_razon')
    criticidad = models.TextField(db_column='criticidad')
    datasheet = models.CharField(max_length=100, db_column='datasheet')
    fecha_precio = models.IntegerField(db_column='fecha_precio')
    Demora = models.IntegerField(db_column='Demora')
    reemplazo = models.IntegerField(db_column='reemplazo')
    id_mate_cat = models.SmallIntegerField(db_column='id_mate_cat')
    esimportado = models.BooleanField(db_column='esimportado')
    relevancia = models.IntegerField(db_column='relevancia')

    class Meta:
        managed = False
        db_table = 'material2'

    def __str__(self):
        return f"Material2 detalles de {self.material.id_mate}"


# ===============================
#   TABLA LEGACY: listamat
# ===============================

class Listamat(models.Model):
    id_listamat = models.AutoField(
        primary_key=True,
        db_column='id_listamat'
    )
    id_mate = models.IntegerField(
        db_column='id_mate',
        null=True,
        blank=True
    )
    critico = models.IntegerField(db_column='critico')
    id_equi = models.IntegerField(
        db_column='id_equi',
        null=True,
        blank=True
    )
    observa = models.CharField(max_length=50, db_column='observa')
    cantidad = models.FloatField(
        db_column='cantidad',
        null=True,
        blank=True
    )
    imprimir = models.SmallIntegerField(db_column='imprimir')

    class Meta:
        managed = False
        db_table = 'listamat'

    def __str__(self):
        return f"Listamat {self.id_listamat} (mate={self.id_mate}, equi={self.id_equi})"

# ===============================
#   TABLA LEGACY: Seguimiento
# ===============================

class Seguimiento(models.Model):
    seg_codigo = models.BigAutoField(
        primary_key=True,
        db_column='SEG_CODIGO'
    )
    seg_numero_serie = models.CharField(
        max_length=255,
        db_column='SEG_NUMERO_SERIE',
        null=True,
        blank=True
    )
    seg_fecha_liberacion = models.DateTimeField(
        db_column='SEG_FECHA_LIBERACION',
        null=True,
        blank=True
    )
    equi_codigo = models.BigIntegerField(
        db_column='EQUI_CODIGO',
        null=True,
        blank=True
    )

    class Meta:
        managed = False
        db_table = 'seguimiento'

    def __str__(self):
        return f"{self.seg_numero_serie} → {self.equi_codigo}"
    
# ===============================
#   PROXY: Repuesto (compatibilidad)
# ===============================

class Repuesto(Material):
    """
    Modelo proxy para mantener compatibilidad con el código
    anterior que importaba 'Repuesto'. No crea tabla nueva.
    """
    class Meta:
        proxy = True
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"

    def __str__(self):
        return f"Repuesto {self.id_mate} - {self.valor}"    