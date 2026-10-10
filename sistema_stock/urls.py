
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [

    # ADMIN
    path("admin/", admin.site.urls),

    # LOGIN / INICIO
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login_page"),

    # RECUPERAR CONTRASEÑA
    path(
        "cuentas/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url="/cuentas/recuperar/enviado/",
        ),
        name="password_reset",
    ),

    path(
        "cuentas/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),

    path(
        "cuentas/restablecer/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url="/cuentas/restablecer/completado/",
        ),
        name="password_reset_confirm",
    ),

    path(
        "cuentas/restablecer/completado/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),

    # CAMBIAR CONTRASEÑA (USUARIO CON SESIÓN INICIADA)
    path(
        "cuentas/contrasena/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
            success_url="/cuentas/contrasena/cambiada/",
        ),
        name="password_change",
    ),

    path(
        "cuentas/contrasena/cambiada/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html",
        ),
        name="password_change_done",
    ),

    # DASHBOARD
    path("dashboard/", views.dashboard, name="dashboard"),

    # USUARIOS
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuarios/nuevo/", views.nuevo_usuario, name="nuevo_usuario"),
    path(
        "usuarios/eliminar/<int:user_id>/",
        views.eliminar_usuario,
        name="eliminar_usuario",
    ),
    path(
        "usuarios/permisos/<int:user_id>/",
        views.permisos_usuario,
        name="permisos_usuario",
    ),

    # AUDITORÍA
    path("auditoria/", views.auditoria, name="auditoria"),

    # PRODUCTOS
    path("productos/", include("productos.urls")),

    # VENTAS
    path("ventas/", include("ventas.urls")),
]


# ARCHIVOS MEDIA
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )