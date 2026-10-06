from django.contrib import admin

from .models import Venta, DetalleVenta, Caja


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "negocio",
        "cliente",
        "fecha",
        "total",
        "tipo_pago",
        "pago",
        "vuelto",
    )

    search_fields = (
        "numero_factura",
        "cliente__nombre",
    )

    list_filter = (
        "negocio",
        "tipo_pago",
        "fecha",
    )


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = (
        "venta",
        "producto",
        "variante",
        "cantidad",
        "precio",
    )

    list_filter = (
        "producto",
        "variante",
    )


@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "negocio",
        "usuario",
        "fecha_apertura",
        "fecha_cierre",
        "monto_inicial",
        "monto_final",
        "estado",
    )

    list_filter = (
        "negocio",
        "estado",
        "usuario",
    )