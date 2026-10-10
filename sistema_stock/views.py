from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils.timezone import localdate

from productos.models import (
    Producto,
    Negocio,
    PermisoUsuario,
    Auditoria,
)

from ventas.models import (
    Venta,
    DetalleVenta,
)


# ==========================================================
# FUNCIONES DE PERMISOS
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
# LOGIN
# ==========================================================

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("/dashboard/")

        return render(
            request,
            "login.html",
            {
                "error": "Usuario o contraseña incorrectos"
            }
        )

    return render(
        request,
        "login.html"
    )


# ==========================================================
# DASHBOARD
# ==========================================================

@login_required
def dashboard(request):

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("/admin/")

    hoy = localdate()

    mes_actual = hoy.month
    anio_actual = hoy.year

    ventas_hoy = (
        Venta.objects
        .filter(
            negocio=negocio,
            fecha__date=hoy
        )
        .aggregate(
            total=Sum("total")
        )["total"]
        or 0
    )

    ventas_mes = (
        Venta.objects
        .filter(
            negocio=negocio,
            fecha__month=mes_actual,
            fecha__year=anio_actual
        )
        .aggregate(
            total=Sum("total")
        )["total"]
        or 0
    )

    ganancia_mes = (
        Venta.objects
        .filter(
            negocio=negocio,
            fecha__month=mes_actual,
            fecha__year=anio_actual
        )
        .aggregate(
            total=Sum("ganancia")
        )["total"]
        or 0
    )

    ventas_total = (
        Venta.objects
        .filter(
            negocio=negocio
        )
        .aggregate(
            total=Sum("total")
        )["total"]
        or 0
    )

    ganancia = (
        Venta.objects
        .filter(
            negocio=negocio
        )
        .aggregate(
            total=Sum("ganancia")
        )["total"]
        or 0
    )

    cantidad_productos = (
        Producto.objects
        .filter(
            negocio=negocio
        )
        .count()
    )

    productos = (
        Producto.objects
        .filter(
            negocio=negocio
        )
        .prefetch_related("variantes")
    )

    productos_bajo = []

    for producto in productos:

        stock_total = sum(
            variante.stock
            for variante in producto.variantes.all()
        )

        producto.stock_total = stock_total

        if stock_total <= 5:
            productos_bajo.append(producto)

    top_productos = (
        DetalleVenta.objects
        .filter(
            venta__negocio=negocio
        )
        .values(
            "producto__nombre"
        )
        .annotate(
            total=Sum("cantidad")
        )
        .order_by("-total")[:5]
    )

    return render(
        request,
        "dashboard.html",
        {
            "negocio": negocio,
            "ventas_hoy": ventas_hoy,
            "ventas_mes": ventas_mes,
            "ganancia_mes": ganancia_mes,
            "ventas_total": ventas_total,
            "ganancia": ganancia,
            "cantidad_productos": cantidad_productos,
            "productos_bajo": productos_bajo,
            "top_productos": top_productos,
        }
    )


# ==========================================================
# USUARIOS
# ==========================================================

@login_required
def usuarios(request):

    if not tiene_permiso(
        request.user,
        "usuarios"
    ):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        propietario=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    usuarios = negocio.usuarios.all()

    return render(
        request,
        "usuarios.html",
        {
            "negocio": negocio,
            "usuarios": usuarios,
        }
    )


# ==========================================================
# NUEVO USUARIO
# ==========================================================

@login_required
def nuevo_usuario(request):

    if not tiene_permiso(
        request.user,
        "usuarios"
    ):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        propietario=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        rol = request.POST.get(
            "rol"
        )

        if not username or not password:

            return render(
                request,
                "nuevo_usuario.html",
                {
                    "error": "Complete todos los campos."
                }
            )

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "nuevo_usuario.html",
                {
                    "error": "Ese usuario ya existe."
                }
            )

        usuario = User.objects.create_user(
            username=username,
            password=password
        )

        if rol == "Admin":

            grupo, created = Group.objects.get_or_create(
                name="Admin"
            )

        else:

            grupo, created = Group.objects.get_or_create(
                name="Cajero"
            )

        usuario.groups.add(grupo)

        negocio.usuarios.add(
            usuario
        )

        # Crear automáticamente los permisos
        # del nuevo usuario.
        PermisoUsuario.objects.get_or_create(
            usuario=usuario
        )

        return redirect(
            "/usuarios/"
        )

    return render(
        request,
        "nuevo_usuario.html"
    )


# ==========================================================
# ELIMINAR USUARIO
# ==========================================================

@login_required
def eliminar_usuario(
    request,
    user_id
):

    if not tiene_permiso(
        request.user,
        "usuarios"
    ):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        propietario=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    usuario = User.objects.filter(
        id=user_id
    ).first()

    if not usuario:
        return redirect(
            "/usuarios/"
        )

    # El propietario no puede eliminarse
    if usuario == negocio.propietario:
        return redirect(
            "/usuarios/"
        )

    if usuario not in negocio.usuarios.all():
        return redirect(
            "/usuarios/"
        )

    negocio.usuarios.remove(
        usuario
    )

    usuario.delete()

    return redirect(
        "/usuarios/"
    )


# ==========================================================
# PERMISOS DE USUARIO
# ==========================================================

@login_required
def permisos_usuario(
    request,
    user_id
):

    if not tiene_permiso(
        request.user,
        "usuarios"
    ):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        propietario=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    usuario = User.objects.filter(
        id=user_id
    ).first()

    if not usuario:
        return redirect(
            "/usuarios/"
        )

    if usuario not in negocio.usuarios.all():
        return redirect(
            "/usuarios/"
        )

    permisos, creado = (
        PermisoUsuario.objects.get_or_create(
            usuario=usuario
        )
    )

    if request.method == "POST":

        permisos.realizar_ventas = (
            "realizar_ventas"
            in request.POST
        )
        permisos.aplicar_descuentos = (
    "aplicar_descuentos"
    in request.POST
)

        permisos.ver_productos = (
            "ver_productos"
            in request.POST
        )

        permisos.agregar_producto = (
            "agregar_producto"
            in request.POST
        )

        permisos.editar_producto = (
            "editar_producto"
            in request.POST
        )

        permisos.eliminar_producto = (
            "eliminar_producto"
            in request.POST
        )

        permisos.clientes = (
            "clientes"
            in request.POST
        )

        permisos.proveedores = (
            "proveedores"
            in request.POST
        )

        permisos.compras = (
            "compras"
            in request.POST
        )

        permisos.reporte_ventas = (
            "reporte_ventas"
            in request.POST
        )

        permisos.graficos = (
            "graficos"
            in request.POST
        )

        permisos.caja = (
            "caja"
            in request.POST
        )

        permisos.usuarios = (
            "usuarios"
            in request.POST
        )

        # Administración técnica queda
        # exclusivamente para el propietario.
        if usuario == negocio.propietario:

            permisos.administracion_tecnica = True

        else:

            permisos.administracion_tecnica = False

        permisos.save()

        return redirect(
            f"/usuarios/permisos/{usuario.id}/"
        )

    return render(
        request,
        "permisos_usuario.html",
        {
            "negocio": negocio,
            "usuario": usuario,
            "permisos": permisos,
        }
    )


# ==========================================================
# AUDITORÍA
# ==========================================================

@login_required
def auditoria(request):

    if not tiene_permiso(
        request.user,
        "administracion_tecnica"
    ):
        return redirect("dashboard")

    negocio = Negocio.objects.filter(
        usuarios=request.user
    ).first()

    if not negocio:
        return redirect("dashboard")

    registros = (
        Auditoria.objects
        .filter(
            negocio=negocio
        )
        .select_related("usuario")
        .order_by("-fecha")
    )

    return render(
        request,
        "auditoria.html",
        {
            "negocio": negocio,
            "registros": registros,
        }
    )