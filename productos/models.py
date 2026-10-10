
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField


class Negocio(models.Model):
    nombre = models.CharField(max_length=100)

    propietario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="negocios_propios"
    )

    usuarios = models.ManyToManyField(
        User,
        related_name="negocios"
    )

    ruc = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    timbrado = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    establecimiento = models.CharField(
        max_length=3,
        default="001"
    )

    punto_expedicion = models.CharField(
        max_length=3,
        default="001"
    )

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Producto general.

    Ejemplo:
    Jean clásico
    Remera básica
    Zapatilla deportiva
    """

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="productos"
    )

    nombre = models.CharField(
        max_length=200
    )

    descripcion = models.TextField(
        blank=True
    )

    codigo = models.CharField(
        max_length=50
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=0
    )

    costo = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0
    )

    imagen = CloudinaryField(
        "imagen",
        blank=True,
        null=True
    )

    activo = models.BooleanField(
        default=True
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["negocio", "codigo"],
                name="codigo_producto_por_negocio"
            )
        ]

    @property
    def margen(self):
        if self.costo > 0:
            return round(
                ((self.precio - self.costo) / self.costo) * 100,
                1
            )

        return 0

    def __str__(self):
        return self.nombre


class VarianteProducto(models.Model):
    """
    Variante de un producto.

    Ejemplo:

    Producto: Jean clásico
    Variante: Azul - Talle 38
    Stock: 3
    """

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="variantes"
    )

    nombre = models.CharField(
        max_length=200
    )

    color = models.CharField(
        max_length=50,
        blank=True
    )

    talle = models.CharField(
        max_length=30,
        blank=True
    )

    medida = models.CharField(
        max_length=50,
        blank=True
    )

    codigo = models.CharField(
        max_length=50,
        blank=True
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    activo = models.BooleanField(
        default=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["producto", "codigo"],
                name="codigo_variante_por_producto"
            )
        ]

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre}"


class Cliente(models.Model):
    nombre = models.CharField(
        max_length=100
    )

    documento = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    direccion = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="clientes"
    )

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre = models.CharField(
        max_length=100
    )

    telefono = models.CharField(
        max_length=20,
        blank=True
    )

    direccion = models.CharField(
        max_length=200,
        blank=True
    )

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        related_name="proveedores"
    )

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE
    )

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    total = models.IntegerField(
        default=0
    )

    def __str__(self):
        return f"Compra {self.id}"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(
        Compra,
        on_delete=models.CASCADE
    )

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE
    )

    variante = models.ForeignKey(
        VarianteProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    cantidad = models.IntegerField()

    precio = models.IntegerField()
    # ==========================================================
# PERMISOS INDIVIDUALES DE USUARIO
# ==========================================================

class PermisoUsuario(models.Model):

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="permisos"
    )

    realizar_ventas = models.BooleanField(default=True)
    aplicar_descuentos = models.BooleanField(default=False)

    ver_productos = models.BooleanField(default=True)

    agregar_producto = models.BooleanField(default=False)

    editar_producto = models.BooleanField(default=False)

    eliminar_producto = models.BooleanField(default=False)

    clientes = models.BooleanField(default=True)

    proveedores = models.BooleanField(default=False)

    compras = models.BooleanField(default=False)

    reporte_ventas = models.BooleanField(default=False)

    graficos = models.BooleanField(default=False)

    caja = models.BooleanField(default=True)

    usuarios = models.BooleanField(default=False)

    administracion_tecnica = models.BooleanField(default=False)

    def __str__(self):
        return f"Permisos de {self.usuario.username}"
    
    # ==========================================================
# AUDITORÍA DEL SISTEMA
# ==========================================================

class Auditoria(models.Model):

    negocio = models.ForeignKey(
        Negocio,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="auditorias"
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias"
    )

    accion = models.CharField(
        max_length=100
    )

    modelo = models.CharField(
        max_length=100,
        blank=True
    )

    objeto_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    descripcion = models.TextField()

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.fecha}"