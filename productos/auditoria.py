from .models import Auditoria


def registrar_auditoria(
    request,
    accion,
    descripcion,
    negocio=None,
    modelo="",
    objeto_id=None
):
    Auditoria.objects.create(
        negocio=negocio,
        usuario=request.user if request.user.is_authenticated else None,
        accion=accion,
        modelo=modelo,
        objeto_id=objeto_id,
        descripcion=descripcion
    )