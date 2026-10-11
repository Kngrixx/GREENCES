"""
auth_controller.py - Registro, login y perfil.

Flujo del login con JWT:
  1. El usuario envia email y password.
  2. Si son correctos, se crea un token firmado con JWT_SECRET_KEY que guarda el
     id del usuario y una fecha de vencimiento.
  3. El frontend envia ese token en cada peticion (Authorization: Bearer <token>)
     y las rutas con @jwt_required() lo verifican antes de responder.
"""
from flask import jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity

from app.services.auth_service import obtener_usuario, registrar_usuario, validar_credenciales


def usuario_a_dict(usuario):
    return {
        "id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email,
        "identificacion": usuario.identificacion,
    }


def registro():
    """POST /api/auth/registro - Crea un usuario (se usa desde Postman)."""
    datos = request.get_json(silent=True) or {}
    nombre_completo = datos.get("nombre_completo")
    email = datos.get("email")
    password = datos.get("password")
    identificacion = datos.get("identificacion")

    if not all(isinstance(v, str) and v.strip() for v in (nombre_completo, email, password, identificacion)):
        return jsonify({"mensaje": "nombre_completo, email, password e identificacion son obligatorios"}), 400
    if "@" not in email:
        return jsonify({"mensaje": "El email no es válido"}), 400
    if len(password) < 6:
        return jsonify({"mensaje": "La contraseña debe tener al menos 6 caracteres"}), 400

    try:
        usuario = registrar_usuario(nombre_completo, email, password, identificacion.strip())
    except ValueError as error:
        return jsonify({"mensaje": str(error)}), 409      # 409 Conflict: ya existe

    return jsonify({"mensaje": "Usuario creado", "usuario": usuario_a_dict(usuario)}), 201


def login():
    """POST /api/auth/login - Verifica las credenciales y entrega el token."""
    datos = request.get_json(silent=True) or {}
    email = datos.get("email")
    password = datos.get("password")
    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        return jsonify({"mensaje": "email y password son obligatorios"}), 400

    usuario = validar_credenciales(email, password)
    if usuario is None:
        # 401 Unauthorized. Mismo mensaje para email o clave incorrectos, para no
        # revelar cuales emails estan registrados.
        return jsonify({"mensaje": "Email o contraseña incorrectos"}), 401

    token = create_access_token(identity=str(usuario.id))
    return jsonify({
        "mensaje": "Inicio de sesión correcto",
        "access_token": token,
        "usuario": usuario_a_dict(usuario),
    }), 200


def perfil():
    """GET /api/auth/perfil - Datos del usuario dueno del token (sirve para validar la sesion)."""
    usuario = obtener_usuario(int(get_jwt_identity()))
    if usuario is None or not usuario.activo:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    return jsonify({"usuario": usuario_a_dict(usuario)}), 200
