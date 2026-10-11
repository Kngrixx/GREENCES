"""
auth_service.py - Registro de usuarios y verificacion de credenciales.

La contrasena se guarda como hash (werkzeug): una huella de un solo sentido. Al
iniciar sesion se calcula la huella de lo que escribio el usuario y se compara;
la contrasena original nunca queda guardada.
"""
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.usuario import Usuario


def registrar_usuario(nombre_completo, email, password, identificacion):
    """Crea un usuario. Lanza ValueError si el email o la identificacion ya existen."""
    email = email.strip().lower()
    if db.session.execute(select(Usuario).where(Usuario.email == email)).scalar_one_or_none():
        raise ValueError("El email ya está registrado")
    if db.session.execute(
            select(Usuario).where(Usuario.identificacion == identificacion)).scalar_one_or_none():
        raise ValueError("La identificación ya está registrada")

    usuario = Usuario(
        nombre_completo=nombre_completo.strip(),
        email=email,
        password_hash=generate_password_hash(password),
        identificacion=identificacion,
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def validar_credenciales(email, password):
    """Devuelve el usuario si el email y la contrasena son correctos; si no, None."""
    usuario = db.session.execute(
        select(Usuario).where(Usuario.email == email.strip().lower())
    ).scalar_one_or_none()
    if usuario is None or not usuario.activo:
        return None
    if not check_password_hash(usuario.password_hash, password):
        return None
    return usuario


def obtener_usuario(usuario_id):
    return db.session.get(Usuario, usuario_id)
