from django.contrib import admin

from .models import (
    Producto,
    VarianteProducto,
    Negocio,
    Cliente,
    Proveedor,
    Compra,
    DetalleCompra,
)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "codigo",
        "negocio",
        "precio",
        "costo",
        "activo",
    )

    search_fields = (
        "nombre",
        "codigo",
    )

    list_filter = (
        "negocio",
        "activo",
    )


@admin.register(VarianteProducto)
class VarianteProductoAdmin(admin.ModelAdmin):
    list_display = (
        "producto",
        "nombre",
        "color",
        "talle",
        "medida",
        "codigo",
        "stock",
        "activo",
    )

    search_fields = (
        "producto__nombre",
        "nombre",
        "codigo",
        "color",
        "talle",
        "medida",
    )

    list_filter = (
        "activo",
    )


@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "propietario",
        "ruc",
        "timbrado",
    )

    search_fields = (
        "nombre",
        "ruc",
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "documento",
        "telefono",
        "negocio",
    )

    search_fields = (
        "nombre",
        "documento",
        "telefono",
    )

    list_filter = (
        "negocio",
    )


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "telefono",
        "negocio",
    )

    search_fields = (
        "nombre",
        "telefono",
    )

    list_filter = (
        "negocio",
    )


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "proveedor",
        "negocio",
        "fecha",
        "total",
    )

    list_filter = (
        "negocio",
        "proveedor",
    )


@admin.register(DetalleCompra)
class DetalleCompraAdmin(admin.ModelAdmin):
    list_display = (
        "compra",
        "producto",
        "variante",
        "cantidad",
        "precio",
    )

    list_filter = (
        "producto",
        "variante",
    )