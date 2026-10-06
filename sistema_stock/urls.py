from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views


urlpatterns = [

    # =========================
    # ADMIN
    # =========================

    path(
        "admin/",
        admin.site.urls
    ),

    # =========================
    # LOGIN / INICIO
    # =========================

    path(
        "",
        views.login_view,
        name="login"
    ),

    path(
        "login/",
        views.login_view,
        name="login_page"
    ),

    # =========================
    # DASHBOARD
    # =========================

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # =========================
    # USUARIOS
    # =========================

    path(
        "usuarios/",
        views.usuarios,
        name="usuarios"
    ),

    path(
        "usuarios/nuevo/",
        views.nuevo_usuario,
        name="nuevo_usuario"
    ),

    path(
        "usuarios/eliminar/<int:user_id>/",
        views.eliminar_usuario,
        name="eliminar_usuario"
    ),

    path(
        "usuarios/permisos/<int:user_id>/",
        views.permisos_usuario,
        name="permisos_usuario"
    ),

    # =========================
    # AUDITORÍA
    # =========================

    path(
        "auditoria/",
        views.auditoria,
        name="auditoria"
    ),

    # =========================
    # PRODUCTOS
    # =========================

    path(
        "productos/",
        include("productos.urls")
    ),

    # =========================
    # VENTAS
    # =========================

    path(
        "ventas/",
        include("ventas.urls")
    ),

]


# =========================
# ARCHIVOS MEDIA
# =========================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )