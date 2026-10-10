from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.contrib import messages

from decimal import Decimal, InvalidOperation

from productos.models import (
    Producto,
    VarianteProducto,
    Cliente,
    Negocio,
    PermisoUsuario,
    Auditoria,
)

from .models import Venta, DetalleVenta, Caja

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def es_admin(user):
    return user.groups.filter(name="Admin").exists()


def tiene_permiso(user, permiso):

    if es_admin(user):
        return True

    permiso_usuario = PermisoUsuario.objects.filter(
        usuario=user
    ).first()

    if not permiso_usuario:
        return False

    return getattr(
        permiso_usuario,
        permiso,
        False
    )


def obtener_negocio(user):
    return Negocio.objects.filter(
        usuarios=user
    ).first()


def convertir_decimal(valor):
    """
    Convierte valores como:

    150000
    150.000
    150,000

    en Decimal.
    """

    if valor is None:
        return Decimal("0")

    valor = str(valor).strip()

    if not valor:
        return Decimal("0")

    valor = (
        valor
        .replace(".", "")
        .replace(",", "")
    )

    try:
        return Decimal(valor)
    except InvalidOperation:
        return Decimal("0")


def registrar_auditoria(
    request,
    negocio,
    accion,
    modelo="",
    objeto_id=None,
    descripcion=""
):
    Auditoria.objects.create(
        negocio=negocio,
        usuario=request.user,
        accion=accion,
        modelo=modelo,
        objeto_id=objeto_id,
        descripcion=descripcion,
    )


# ============================================================
# PDF DE VENTA
# ============================================================

@login_required
def generar_pdf(request, venta_id):

    negocio = obtener_negocio(request.user)

    if not negocio:
        return redirect("dashboard")

    venta = get_object_or_404(
        Venta,
        id=venta_id,
        negocio=negocio
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="venta_{venta.id}.pdf"'
    )

    p = canvas.Canvas(
        response,
        pagesize=letter
    )

    ancho, alto = letter

    y = alto - 40

    p.setFont(
        "Helvetica-Bold",
        16
    )

    p.drawString(
        40,
        y,
        negocio.nombre
    )

    y -= 25

    p.setFont(
        "Helvetica",
        10
    )

    p.drawString(
        40,
        y,
        f"Venta N°: {venta.id}"
    )

    y -= 15

    p.drawString(
        40,
        y,
        f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}"
    )

    y -= 30

    p.setFont(
        "Helvetica-Bold",
        10
    )

    p.drawString(
        40,
        y,
        "Producto"
    )

    p.drawString(
        300,
        y,
        "Cantidad"
    )

    p.drawString(
        390,
        y,
        "Precio"
    )

    p.drawString(
        470,
        y,
        "Subtotal"
    )

    y -= 15

    p.setFont(
        "Helvetica",
        9
    )

    for detalle in venta.detalles.all():

        nombre = detalle.producto.nombre[:35]

        subtotal = (
            detalle.cantidad *
            detalle.precio
        )

        p.drawString(
            40,
            y,
            nombre
        )

        p.drawString(
            300,
            y,
            str(detalle.cantidad)
        )

        p.drawString(
            390,
            y,
            f"Gs. {detalle.precio:,.0f}"
        )

        p.drawString(
            470,
            y,
            f"Gs. {subtotal:,.0f}"
        )

        y -= 15

        if y < 50:

            p.showPage()

            y = alto - 40

            p.setFont(
                "Helvetica",
                9
            )

    y -= 15

    p.setFont(
        "Helvetica-Bold",
        12
    )

    p.drawString(
        350,
        y,
        f"TOTAL: Gs. {venta.total:,.0f}"
    )

    y -= 20

    p.setFont(
        "Helvetica",
        10
    )

    p.drawString(
        350,
        y,
        f"Pago: Gs. {venta.pago:,.0f}"
    )

    y -= 15

    p.drawString(
        350,
        y,
        f"Vuelto: Gs. {venta.vuelto:,.0f}"
    )

    y -= 15

    p.drawString(
        350,
        y,
        f"Descuento: Gs. {venta.descuento:,.0f}"
    )

    p.showPage()

    p.save()

    return response


# ============================================================
# NUEVA VENTA
# ============================================================

@login_required
def nueva_venta(request):

    negocio = obtener_negocio(
        request.user
    )

    if not negocio:

        messages.error(
            request,
            "No tenés un negocio asignado."
        )

        return redirect(
            "dashboard"
        )

    if not tiene_permiso(
        request.user,
        "realizar_ventas"
    ):

        messages.error(
            request,
            "No tenés permiso para realizar ventas."
        )

        return redirect(
            "dashboard"
        )

    # ========================================================
    # VERIFICAR CAJA ABIERTA
    # ========================================================

    caja_abierta = (
        Caja.objects
        .filter(
            negocio=negocio,
            estado="abierta"
        )
        .first()
    )

    if not caja_abierta:

        messages.warning(
            request,
            "Primero debés abrir la caja para realizar ventas."
        )

        return redirect(
            "/ventas/caja/abrir/"
        )

    clientes = Cliente.objects.filter(
        negocio=negocio
    )

    productos = (
        Producto.objects
        .filter(
            negocio=negocio,
            activo=True
        )
        .prefetch_related(
            "variantes"
        )
    )

    # ========================================================
    # POST - REALIZAR VENTA
    # ========================================================

    if request.method == "POST":

        caja_abierta = (
            Caja.objects
            .filter(
                negocio=negocio,
                estado="abierta"
            )
            .first()
        )

        if not caja_abierta:

            messages.error(
                request,
                "La caja está cerrada. Primero debés abrir una caja."
            )

            return redirect(
                "/ventas/caja/abrir/"
            )

        # ----------------------------------------------------
        # CLIENTE
        # ----------------------------------------------------

        cliente_id = request.POST.get(
            "cliente"
        )

        cliente = None

        if cliente_id:

            cliente = Cliente.objects.filter(
                id=cliente_id,
                negocio=negocio
            ).first()

# ----------------------------------------------------
# DESCUENTO Y VALIDACIÓN DE PERMISOS
# ----------------------------------------------------

    descuento = convertir_decimal(
        request.POST.get(
          "descuento",
         "0"
     )
    )

    es_administrador = request.user.is_superuser or request.user.groups.filter(
      name="Admin"
    ).exists()

    permite_descuentos = (
        es_administrador
        or tiene_permiso(
         request.user,
         "aplicar_descuentos"
        )
    )

    if not permite_descuentos:
        descuento = Decimal("0")

    if descuento < 0:
        descuento = Decimal("0")
        # ----------------------------------------------------
        # TIPO DE PAGO
        # ----------------------------------------------------

        tipo_pago = request.POST.get(
            "tipo_pago",
            "efectivo"
        )

        if tipo_pago not in [
            "efectivo",
            "transferencia"
        ]:

            tipo_pago = "efectivo"

        # ----------------------------------------------------
        # PAGO
        # ----------------------------------------------------

        pago = convertir_decimal(
            request.POST.get(
                "pago",
                "0"
            )
        )

        if pago < 0:

            pago = Decimal("0")

        # ----------------------------------------------------
        # RECORRER PRODUCTOS DEL CARRITO
        # ----------------------------------------------------

        items = []

        total = Decimal("0")

        ganancia_total = Decimal("0")

        error_stock = False

        for key, value in request.POST.items():

            if not key.startswith(
                "cantidad_"
            ):

                continue

            try:

                variante_id = int(
                    key.split("_")[1]
                )

                cantidad = int(
                    value or 0
                )

            except (
                ValueError,
                IndexError
            ):

                continue

            if cantidad <= 0:

                continue

            variante = (
                VarianteProducto.objects
                .select_related(
                    "producto"
                )
                .filter(
                    id=variante_id,
                    producto__negocio=negocio,
                    producto__activo=True
                )
                .first()
            )

            if not variante:

                continue

            if cantidad > variante.stock:

                error_stock = True

                break

            producto = variante.producto

            precio = (
                producto.precio
            )

            costo = (
                producto.costo
            )

            subtotal = (
                precio *
                cantidad
            )

            ganancia_producto = (
                precio -
                costo
            ) * cantidad

            total += subtotal

            ganancia_total += (
                ganancia_producto
            )

            items.append({
                "variante": variante,
                "producto": producto,
                "cantidad": cantidad,
                "precio": precio,
            })

        # ----------------------------------------------------
        # VALIDAR STOCK
        # ----------------------------------------------------

        if error_stock:

            messages.error(
                request,
                "Una de las cantidades supera el stock disponible."
            )

            return redirect(
                "ventas"
            )

        # ----------------------------------------------------
        # VALIDAR CARRITO
        # ----------------------------------------------------

        if not items or total <= 0:

            messages.error(
                request,
                "No hay productos en la venta."
            )

            return redirect(
                "ventas"
            )

        # ----------------------------------------------------
        # TOTAL FINAL
        # ----------------------------------------------------

        total_final = (
            total -
            descuento
        )

        if total_final < 0:

            total_final = Decimal("0")

        if total_final <= 0:

            messages.error(
                request,
                "El total de la venta debe ser mayor a 0."
            )

            return redirect(
                "ventas"
            )

        # ----------------------------------------------------
        # VALIDAR PAGO
        # ----------------------------------------------------

        if pago < total_final:

            messages.error(
                request,
                "El pago recibido es menor al total."
            )

            return redirect(
                "ventas"
            )

        # ----------------------------------------------------
        # GANANCIA FINAL
        # ----------------------------------------------------

        ganancia_total -= descuento

        if ganancia_total < 0:

            ganancia_total = Decimal("0")

        # ----------------------------------------------------
        # VUELTO
        # ----------------------------------------------------

        vuelto = (
            pago -
            total_final
        )

        # ----------------------------------------------------
        # NÚMERO DE FACTURA
        # ----------------------------------------------------

        ultima = (
            Venta.objects
            .filter(
                negocio=negocio
            )
            .exclude(
                numero_factura=""
            )
            .order_by("-id")
            .first()
        )

        numero = 1

        if ultima:

            try:

                numero = (
                    int(
                        ultima.numero_factura
                        .split("-")[-1]
                    ) + 1
                )

            except (
                ValueError,
                IndexError
            ):

                numero = 1

        numero_factura = (
            f"{negocio.establecimiento}-"
            f"{negocio.punto_expedicion}-"
            f"{str(numero).zfill(7)}"
        )

        # ----------------------------------------------------
        # CREAR VENTA
        # ----------------------------------------------------

        venta = Venta.objects.create(

            negocio=negocio,

            caja=caja_abierta,

            cliente=cliente,

            numero_factura=numero_factura,

            timbrado=(
                negocio.timbrado or ""
            ),

            total=total_final,

            descuento=descuento,

            ganancia=int(
                ganancia_total
            ),

            tipo_pago=tipo_pago,

            pago=float(
                pago
            ),

            vuelto=float(
                vuelto
            )
        )

        # ----------------------------------------------------
        # CREAR DETALLES Y DESCONTAR STOCK
        # ----------------------------------------------------

        for item in items:

            variante = item[
                "variante"
            ]

            producto = item[
                "producto"
            ]

            cantidad = item[
                "cantidad"
            ]

            precio = item[
                "precio"
            ]

            DetalleVenta.objects.create(

                venta=venta,

                producto=producto,

                variante=variante,

                cantidad=cantidad,

                precio=precio
            )

            variante.stock -= cantidad

            variante.save()

        # ----------------------------------------------------
        # AUDITORÍA DE LA VENTA
        # ----------------------------------------------------

        productos_auditoria = []

        for item in items:

            producto = item["producto"]
            variante = item["variante"]
            cantidad = item["cantidad"]
            precio = item["precio"]

            subtotal = (
                precio *
                cantidad
            )

            nombre_variante = (
                variante.nombre
                if variante.nombre
                else "Sin variante"
            )

            productos_auditoria.append(
                f"{producto.nombre} "
                f"({nombre_variante}) - "
                f"Cantidad: {cantidad} - "
                f"Precio: Gs. {precio:,.0f} - "
                f"Subtotal: Gs. {subtotal:,.0f}"
            )

        descripcion_venta = (
            f"Factura: {numero_factura} | "
            f"Total: Gs. {total_final:,.0f} | "
            f"Descuento: Gs. {descuento:,.0f} | "
            f"Pago: Gs. {pago:,.0f} | "
            f"Vuelto: Gs. {vuelto:,.0f} | "
            f"Forma de pago: {tipo_pago} | "
            f"Productos: "
            + " || ".join(
                productos_auditoria
            )
        )

        registrar_auditoria(
            request=request,
            negocio=negocio,
            accion="CREAR_VENTA",
            modelo="Venta",
            objeto_id=venta.id,
            descripcion=descripcion_venta
        )

        # ----------------------------------------------------
        # VENTA CORRECTA
        # ----------------------------------------------------

        messages.success(
            request,
            "Venta realizada correctamente."
        )

        return redirect(
            "ticket",
            venta_id=venta.id
        )

    # ========================================================
    # MOSTRAR PANTALLA DE VENTA
    # ========================================================

    return render(
    request,
    "ventas.html",
    {
        "productos": productos,
        "clientes": clientes,
        "caja_abierta": caja_abierta,
        "permite_descuentos": (
            request.user.is_superuser
            or request.user.groups.filter(
                name="Admin"
            ).exists()
            or tiene_permiso(
                request.user,
                "aplicar_descuentos"
            )
        ),
    }
)


# ============================================================
# REPORTE DE VENTAS
# ============================================================

@login_required
def reporte_ventas(request):

    negocio = obtener_negocio(request.user)

    if not negocio:
        return redirect("dashboard")

    if not tiene_permiso(
        request.user,
        "reporte_ventas"
    ):

        messages.error(
            request,
            "No tenés permiso para ver el reporte de ventas."
        )

        return redirect("dashboard")

    ventas = (
        Venta.objects
        .filter(
            negocio=negocio
        )
        .prefetch_related(
            "detalles__producto",
            "detalles__variante"
        )
        .order_by("-fecha")
    )

    total_vendido = (
        ventas.aggregate(
            total=Sum("total")
        )["total"] or 0
    )

    total_ganancia = (
        ventas.aggregate(
            total=Sum("ganancia")
        )["total"] or 0
    )

    return render(
        request,
        "reporte.html",
        {
            "ventas": ventas,
            "total_vendido": total_vendido,
            "total_ganancia": total_ganancia,
        }
    )


# ============================================================
# TICKET
# ============================================================

@login_required
def ticket(request, venta_id):

    negocio = obtener_negocio(
        request.user
    )

    if not negocio:

        return redirect(
            "dashboard"
        )

    venta = get_object_or_404(
        Venta,
        id=venta_id,
        negocio=negocio
    )

    detalles = (
        DetalleVenta.objects
        .filter(
            venta=venta
        )
        .select_related(
            "producto",
            "variante"
        )
    )

    return render(
        request,
        "ticket.html",
        {
            "venta": venta,
            "detalles": detalles,
            "negocio": negocio,
        }
    )


# ============================================================
# GRÁFICO DE VENTAS
# ============================================================

@login_required
def grafico_ventas(request):

    negocio = obtener_negocio(
        request.user
    )

    if not negocio:

        return redirect(
            "dashboard"
        )

    if not tiene_permiso(
        request.user,
        "graficos"
    ):

        messages.error(
            request,
            "No tenés permiso para ver los gráficos."
        )

        return redirect(
            "dashboard"
        )

    ventas = (
        Venta.objects
        .filter(
            negocio=negocio
        )
        .annotate(
            dia=TruncDate(
                "fecha"
            )
        )
        .values(
            "dia"
        )
        .annotate(
            total=Sum(
                "total"
            )
        )
        .order_by(
            "dia"
        )
    )

    top_productos = (
        DetalleVenta.objects
        .filter(
            venta__negocio=negocio
        )
        .values(
            "producto__nombre"
        )
        .annotate(
            total=Sum(
                "cantidad"
            )
        )
        .order_by(
            "-total"
        )[:5]
    )

    labels = []

    data = []

    for venta in ventas:

        if venta["dia"]:

            labels.append(
                venta["dia"].strftime(
                    "%d-%m"
                )
            )

            data.append(
                float(
                    venta["total"]
                )
            )

    return render(
        request,
        "grafico.html",
        {
            "labels": labels,
            "data": data,
            "top_productos": top_productos,
        }
    )


# ============================================================
# ABRIR CAJA
# ============================================================

@login_required
def abrir_caja(request):

    if not tiene_permiso(request.user, "caja"):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    caja_abierta = Caja.objects.filter(
        negocio=negocio,
        estado="abierta"
    ).first()

    if caja_abierta:
        messages.warning(
            request,
            "Ya existe una caja abierta para este negocio."
        )
        return redirect("ventas")

    if request.method == "POST":

        monto_inicial = request.POST.get("monto_inicial")

        try:
            monto_inicial = Decimal(monto_inicial)

            if monto_inicial < 0:
                raise InvalidOperation

        except (InvalidOperation, TypeError):
            messages.error(
                request,
                "Ingresá un monto inicial válido."
            )

            return render(
                request,
                "abrir_caja.html"
            )

        caja = Caja.objects.create(
            negocio=negocio,
            usuario=request.user,
            monto_inicial=monto_inicial,
            estado="abierta"
        )

        # ----------------------------------------------------
        # AUDITORÍA APERTURA DE CAJA
        # ----------------------------------------------------

        registrar_auditoria(
            request=request,
            negocio=negocio,
            accion="ABRIR_CAJA",
            modelo="Caja",
            objeto_id=caja.id,
            descripcion=(
                f"Caja abierta con monto inicial de "
                f"Gs. {monto_inicial:,.0f}."
            )
        )

        messages.success(
            request,
            "Caja abierta correctamente."
        )

        return redirect("ventas")

    return render(
        request,
        "abrir_caja.html"
    )


# ============================================================
# CERRAR CAJA
# ============================================================

@login_required
def cerrar_caja(request):

    if not tiene_permiso(request.user, "caja"):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    caja = Caja.objects.filter(
        negocio=negocio,
        estado="abierta"
    ).first()

    if not caja:
        messages.warning(
            request,
            "No hay una caja abierta."
        )

        return redirect("ventas")

    ventas_caja = Venta.objects.filter(
        caja=caja
    )

    efectivo = ventas_caja.filter(
        tipo_pago="efectivo"
    ).aggregate(
        total=Sum("total")
    )["total"] or Decimal("0")

    transferencia = ventas_caja.filter(
        tipo_pago="transferencia"
    ).aggregate(
        total=Sum("total")
    )["total"] or Decimal("0")

    total_ventas = efectivo + transferencia

    efectivo_esperado = (
        caja.monto_inicial + efectivo
    )

    if request.method == "POST":

        efectivo_contado = request.POST.get(
            "efectivo_contado"
        )

        observaciones = request.POST.get(
            "observaciones",
            ""
        ).strip()

        try:
            efectivo_contado = Decimal(
                efectivo_contado
            )

        except (InvalidOperation, TypeError):
            messages.error(
                request,
                "Ingresá un efectivo contado válido."
            )

            return render(
                request,
                "cierre_caja.html",
                {
                    "caja": caja,
                    "efectivo": efectivo,
                    "transferencia": transferencia,
                    "total": total_ventas,
                    "total_ventas": total_ventas,
                    "monto_final": efectivo_esperado,
                    "efectivo_esperado": efectivo_esperado,
                }
            )

        diferencia = (
            efectivo_contado - efectivo_esperado
        )

        caja.monto_final = efectivo_contado
        caja.efectivo_contado = efectivo_contado
        caja.diferencia = diferencia
        caja.observaciones = observaciones
        caja.usuario_cierre = request.user
        caja.fecha_cierre = now()
        caja.estado = "cerrada"

        caja.save()

        # ----------------------------------------------------
        # AUDITORÍA CIERRE DE CAJA
        # ----------------------------------------------------

        registrar_auditoria(
            request=request,
            negocio=negocio,
            accion="CERRAR_CAJA",
            modelo="Caja",
            objeto_id=caja.id,
            descripcion=(
                f"Total ventas: Gs. {total_ventas:,.0f} | "
                f"Efectivo: Gs. {efectivo:,.0f} | "
                f"Transferencia: Gs. {transferencia:,.0f} | "
                f"Efectivo esperado: Gs. {efectivo_esperado:,.0f} | "
                f"Efectivo contado: Gs. {efectivo_contado:,.0f} | "
                f"Diferencia: Gs. {diferencia:,.0f} | "
                f"Observaciones: {observaciones or 'Sin observaciones'}"
            )
        )

        messages.success(
            request,
            "Caja cerrada correctamente."
        )

        return redirect("historial_cajas")

    return render(
        request,
        "cierre_caja.html",
        {
            "caja": caja,
            "efectivo": efectivo,
            "transferencia": transferencia,
            "total": total_ventas,
            "total_ventas": total_ventas,
            "monto_final": efectivo_esperado,
            "efectivo_esperado": efectivo_esperado,
        }
    )


# ============================================================
# HISTORIAL DE CAJAS
# ============================================================

@login_required
def historial_cajas(request):

    if not tiene_permiso(request.user, "caja"):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    cajas = Caja.objects.filter(
        negocio=negocio
    ).select_related(
        "usuario",
        "usuario_cierre"
    ).order_by(
        "-fecha_apertura"
    )

    for caja in cajas:

        ventas_caja = Venta.objects.filter(
            caja=caja
        )

        caja.total_efectivo = ventas_caja.filter(
            tipo_pago="efectivo"
        ).aggregate(
            total=Sum("total")
        )["total"] or Decimal("0")

        caja.total_transferencia = ventas_caja.filter(
            tipo_pago="transferencia"
        ).aggregate(
            total=Sum("total")
        )["total"] or Decimal("0")

        caja.total_vendido = (
            caja.total_efectivo +
            caja.total_transferencia
        )

        caja.efectivo_esperado = (
            caja.monto_inicial +
            caja.total_efectivo
        )

    return render(
        request,
        "historial_cajas.html",
        {
            "cajas": cajas
        }
    )