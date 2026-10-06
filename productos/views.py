from django.shortcuts import render, redirect

from productos.models import (
    Producto,
    VarianteProducto,
    Negocio,
    Cliente,
    Proveedor,
    Compra,
    DetalleCompra,
    PermisoUsuario,
    Auditoria,
)

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse

import openpyxl


# ==========================================================
# PERMISOS
# ==========================================================

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


# ==========================================================
# AUDITORÍA
# ==========================================================

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


# ==========================================================
# PRODUCTOS
# ==========================================================

@login_required
def agregar_producto(request):

    if not tiene_permiso(
        request.user,
        "agregar_producto"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    if request.method == "POST":

        nombre = request.POST.get(
            "nombre",
            ""
        ).strip()

        codigo = request.POST.get(
            "codigo",
            ""
        ).strip()

        descripcion = request.POST.get(
            "descripcion",
            ""
        ).strip()

        precio = request.POST.get(
            "precio"
        ) or 0

        costo = request.POST.get(
            "costo"
        ) or 0

        imagen = request.FILES.get(
            "imagen"
        )

        producto = Producto.objects.create(
            negocio=negocio,
            nombre=nombre,
            descripcion=descripcion,
            codigo=codigo,
            precio=precio,
            costo=costo,
            imagen=imagen,
        )

        # ==================================================
        # AUDITORÍA - CREAR PRODUCTO
        # ==================================================

        registrar_auditoria(
            request,
            negocio,
            "CREAR_PRODUCTO",
            "Producto",
            producto.id,
            f"Creó el producto '{producto.nombre}' "
            f"con código '{producto.codigo}'."
        )

        nombres = request.POST.getlist(
            "variante_nombre[]"
        )

        colores = request.POST.getlist(
            "variante_color[]"
        )

        talles = request.POST.getlist(
            "variante_talle[]"
        )

        medidas = request.POST.getlist(
            "variante_medida[]"
        )

        codigos = request.POST.getlist(
            "variante_codigo[]"
        )

        stocks = request.POST.getlist(
            "variante_stock[]"
        )

        for i in range(len(nombres)):

            nombre_variante = nombres[i].strip()

            if not nombre_variante:
                continue

            color = (
                colores[i].strip()
                if i < len(colores)
                else ""
            )

            talle = (
                talles[i].strip()
                if i < len(talles)
                else ""
            )

            medida = (
                medidas[i].strip()
                if i < len(medidas)
                else ""
            )

            codigo_variante = (
                codigos[i].strip()
                if i < len(codigos)
                else ""
            )

            stock = (
                stocks[i]
                if i < len(stocks)
                else 0
            )

            VarianteProducto.objects.create(
                producto=producto,
                nombre=nombre_variante,
                color=color,
                talle=talle,
                medida=medida,
                codigo=codigo_variante,
                stock=stock or 0,
            )

        return redirect("/productos/")

    return render(
        request,
        "agregar_producto.html"
    )


@login_required
def lista_productos(request):

    if not tiene_permiso(
        request.user,
        "ver_productos"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    query = request.GET.get("q")

    productos = (
        Producto.objects
        .filter(
            negocio=negocio
        )
        .prefetch_related("variantes")
    )

    for producto in productos:

        producto.stock_total = sum(
            variante.stock
            for variante in producto.variantes.all()
        )

    if query:

        productos = productos.filter(
            Q(nombre__icontains=query)
            |
            Q(codigo__icontains=query)
        )

        for producto in productos:

            producto.stock_total = sum(
                variante.stock
                for variante in producto.variantes.all()
            )

    return render(
        request,
        "productos.html",
        {
            "productos": productos,
            "query": query,
        },
    )


@login_required
def editar_producto(request, id):

    if not tiene_permiso(
        request.user,
        "editar_producto"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    producto = Producto.objects.filter(
        id=id,
        negocio=negocio
    ).first()

    if not producto:
        return redirect("/productos/")

    if request.method == "POST":

        producto.nombre = request.POST.get(
            "nombre",
            ""
        ).strip()

        producto.codigo = request.POST.get(
            "codigo",
            ""
        ).strip()

        producto.descripcion = request.POST.get(
            "descripcion",
            ""
        ).strip()

        producto.precio = (
            request.POST.get("precio")
            or 0
        )

        producto.costo = (
            request.POST.get("costo")
            or 0
        )

        imagen = request.FILES.get(
            "imagen"
        )

        if imagen:
            producto.imagen = imagen

        producto.save()

        # ==================================================
        # AUDITORÍA - EDITAR PRODUCTO
        # ==================================================

        registrar_auditoria(
            request,
            negocio,
            "EDITAR_PRODUCTO",
            "Producto",
            producto.id,
            f"Editó el producto '{producto.nombre}' "
            f"con código '{producto.codigo}'."
        )

        variante_ids = request.POST.getlist(
            "variante_id[]"
        )

        nombres = request.POST.getlist(
            "variante_nombre[]"
        )

        colores = request.POST.getlist(
            "variante_color[]"
        )

        talles = request.POST.getlist(
            "variante_talle[]"
        )

        medidas = request.POST.getlist(
            "variante_medida[]"
        )

        codigos = request.POST.getlist(
            "variante_codigo[]"
        )

        stocks = request.POST.getlist(
            "variante_stock[]"
        )

        variantes_mantenidas = []

        for i in range(len(nombres)):

            nombre_variante = (
                nombres[i].strip()
                if i < len(nombres)
                else ""
            )

            if not nombre_variante:
                continue

            variante_id = (
                variante_ids[i].strip()
                if i < len(variante_ids)
                else ""
            )

            color = (
                colores[i].strip()
                if i < len(colores)
                else ""
            )

            talle = (
                talles[i].strip()
                if i < len(talles)
                else ""
            )

            medida = (
                medidas[i].strip()
                if i < len(medidas)
                else ""
            )

            codigo_variante = (
                codigos[i].strip()
                if i < len(codigos)
                else ""
            )

            stock = (
                stocks[i]
                if i < len(stocks)
                else 0
            )

            if variante_id:

                variante = VarianteProducto.objects.filter(
                    id=variante_id,
                    producto=producto
                ).first()

                if variante:

                    variante.nombre = (
                        nombre_variante
                    )

                    variante.color = color
                    variante.talle = talle
                    variante.medida = medida
                    variante.codigo = codigo_variante
                    variante.stock = stock or 0

                    variante.save()

                    variantes_mantenidas.append(
                        variante.id
                    )

            else:

                variante = VarianteProducto.objects.create(
                    producto=producto,
                    nombre=nombre_variante,
                    color=color,
                    talle=talle,
                    medida=medida,
                    codigo=codigo_variante,
                    stock=stock or 0,
                )

                variantes_mantenidas.append(
                    variante.id
                )

        VarianteProducto.objects.filter(
            producto=producto
        ).exclude(
            id__in=variantes_mantenidas
        ).delete()

        return redirect("/productos/")

    return render(
        request,
        "editar_producto.html",
        {
            "producto": producto
        }
    )


@login_required
def eliminar_producto(request, id):

    if not tiene_permiso(
        request.user,
        "eliminar_producto"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    producto = Producto.objects.filter(
        id=id,
        negocio=negocio
    ).first()

    if producto:

        nombre_producto = producto.nombre
        codigo_producto = producto.codigo
        producto_id = producto.id

        # ==================================================
        # AUDITORÍA - ELIMINAR PRODUCTO
        # ==================================================

        registrar_auditoria(
            request,
            negocio,
            "ELIMINAR_PRODUCTO",
            "Producto",
            producto_id,
            f"Eliminó el producto '{nombre_producto}' "
            f"con código '{codigo_producto}'."
        )

        producto.delete()

    return redirect("/productos/")


# ==========================================================
# CLIENTES
# ==========================================================

@login_required
def lista_clientes(request):

    if not tiene_permiso(
        request.user,
        "clientes"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    query = request.GET.get("q")

    clientes = Cliente.objects.filter(
        negocio=negocio
    )

    if query:

        clientes = clientes.filter(
            nombre__icontains=query
        )

    return render(
        request,
        "clientes.html",
        {
            "clientes": clientes
        }
    )


@login_required
def agregar_cliente(request):

    if not tiene_permiso(
        request.user,
        "clientes"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    if request.method == "POST":

        nombre = request.POST["nombre"]

        documento = request.POST["documento"]

        Cliente.objects.create(
            nombre=nombre,
            documento=documento,
            negocio=negocio
        )

        return redirect(
            "/productos/clientes/"
        )

    return render(
        request,
        "agregar_cliente.html"
    )


@login_required
def editar_cliente(request, id):

    if not tiene_permiso(
        request.user,
        "clientes"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    cliente = Cliente.objects.filter(
        id=id,
        negocio=negocio
    ).first()

    if not cliente:
        return redirect(
            "/productos/clientes/"
        )

    if request.method == "POST":

        cliente.nombre = request.POST["nombre"]

        cliente.documento = request.POST["documento"]

        cliente.save()

        return redirect(
            "/productos/clientes/"
        )

    return render(
        request,
        "editar_cliente.html",
        {
            "cliente": cliente
        }
    )


@login_required
def eliminar_cliente(request, id):

    if not tiene_permiso(
        request.user,
        "clientes"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    cliente = Cliente.objects.filter(
        id=id,
        negocio=negocio
    ).first()

    if cliente:
        cliente.delete()

    return redirect(
        "/productos/clientes/"
    )


# ==========================================================
# PROVEEDORES
# ==========================================================

@login_required
def lista_proveedores(request):

    if not tiene_permiso(
        request.user,
        "proveedores"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    proveedores = Proveedor.objects.filter(
        negocio=negocio
    )

    return render(
        request,
        "proveedores.html",
        {
            "proveedores": proveedores
        }
    )


@login_required
def agregar_proveedor(request):

    if not tiene_permiso(
        request.user,
        "proveedores"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    if request.method == "POST":

        Proveedor.objects.create(
            nombre=request.POST["nombre"],
            telefono=request.POST["telefono"],
            direccion=request.POST["direccion"],
            negocio=negocio,
        )

        return redirect(
            "/productos/proveedores/"
        )

    return render(
        request,
        "agregar_proveedor.html"
    )


@login_required
def editar_proveedor(request, id):

    if not tiene_permiso(
        request.user,
        "proveedores"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    proveedor = Proveedor.objects.filter(
        id=id,
        negocio=negocio
    ).first()

    if not proveedor:
        return redirect(
            "/productos/proveedores/"
        )

    if request.method == "POST":

        proveedor.nombre = request.POST["nombre"]

        proveedor.telefono = request.POST["telefono"]

        proveedor.direccion = request.POST["direccion"]

        proveedor.save()

        return redirect(
            "/productos/proveedores/"
        )

    return render(
        request,
        "editar_proveedor.html",
        {
            "proveedor": proveedor
        }
    )


@login_required
def eliminar_proveedor(request, id):

    if not tiene_permiso(
        request.user,
        "proveedores"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    proveedor = Proveedor.objects.filter(
        id=id,
        negocio=negocio
    ).first()

    if proveedor:
        proveedor.delete()

    return redirect(
        "/productos/proveedores/"
    )


# ==========================================================
# COMPRAS
# ==========================================================

@login_required
def lista_compras(request):

    if not tiene_permiso(
        request.user,
        "compras"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    compras = Compra.objects.filter(
        negocio=negocio
    )

    return render(
        request,
        "compras.html",
        {
            "compras": compras
        }
    )


@login_required
def nueva_compra(request):

    if not tiene_permiso(
        request.user,
        "compras"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    productos = (
        Producto.objects
        .filter(
            negocio=negocio,
            activo=True
        )
        .prefetch_related("variantes")
    )

    proveedores = Proveedor.objects.filter(
        negocio=negocio
    )

    if request.method == "POST":

        producto_id = request.POST.get(
            "producto"
        )

        variante_id = request.POST.get(
            "variante"
        )

        proveedor_id = request.POST.get(
            "proveedor"
        )

        try:

            cantidad = int(
                request.POST.get(
                    "cantidad",
                    0
                )
            )

        except ValueError:

            cantidad = 0

        try:

            precio = int(
                request.POST.get(
                    "precio",
                    0
                )
            )

        except ValueError:

            precio = 0

        producto = Producto.objects.filter(
            id=producto_id,
            negocio=negocio
        ).first()

        variante = VarianteProducto.objects.filter(
            id=variante_id,
            producto=producto
        ).first()

        proveedor = Proveedor.objects.filter(
            id=proveedor_id,
            negocio=negocio
        ).first()

        if (
            not producto
            or not variante
            or not proveedor
            or cantidad <= 0
            or precio < 0
        ):

            return redirect(
                "/productos/compras/nueva/"
            )

        total = cantidad * precio

        compra = Compra.objects.create(
            proveedor=proveedor,
            negocio=negocio,
            total=total
        )

        DetalleCompra.objects.create(
            compra=compra,
            producto=producto,
            variante=variante,
            cantidad=cantidad,
            precio=precio
        )

        variante.stock += cantidad

        variante.save()

        # ==================================================
        # AUDITORÍA - CREAR COMPRA
        # ==================================================

        nombre_variante = (
            variante.nombre
            if variante.nombre
            else "Sin variante"
        )

        descripcion_compra = (
            f"Proveedor: {proveedor.nombre} | "
            f"Producto: {producto.nombre} | "
            f"Variante: {nombre_variante} | "
            f"Cantidad: {cantidad} | "
            f"Precio unitario: Gs. {precio:,.0f} | "
            f"Total: Gs. {total:,.0f}"
        )

        registrar_auditoria(
            request,
            negocio,
            "CREAR_COMPRA",
            "Compra",
            compra.id,
            descripcion_compra
        )

        return redirect(
            "/productos/compras/"
        )

    return render(
        request,
        "nueva_compra.html",
        {
            "productos": productos,
            "proveedores": proveedores,
        },
    )


# ==========================================================
# EXCEL
# ==========================================================

@login_required
def exportar_excel(request):

    if not tiene_permiso(
        request.user,
        "ver_productos"
    ):
        return redirect("/dashboard/")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/dashboard/")

    productos = (
        Producto.objects
        .filter(
            negocio=negocio
        )
        .prefetch_related("variantes")
    )

    workbook = openpyxl.Workbook()

    sheet = workbook.active

    sheet.title = "Productos"

    headers = [
        "Producto",
        "Código Producto",
        "Variante",
        "Código Variante",
        "Color",
        "Talle",
        "Medida",
        "Precio",
        "Costo",
        "Stock",
    ]

    sheet.append(headers)

    for producto in productos:

        variantes = producto.variantes.all()

        if variantes:

            for variante in variantes:

                sheet.append([
                    producto.nombre,
                    producto.codigo,
                    variante.nombre,
                    variante.codigo,
                    variante.color,
                    variante.talle,
                    variante.medida,
                    producto.precio,
                    producto.costo,
                    variante.stock,
                ])

        else:

            sheet.append([
                producto.nombre,
                producto.codigo,
                "",
                "",
                "",
                "",
                "",
                producto.precio,
                producto.costo,
                0,
            ])

    response = HttpResponse(
        content_type=(
            "application/vnd."
            "openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )

    response["Content-Disposition"] = (
        'attachment; filename="productos.xlsx"'
    )

    workbook.save(response)

    return response