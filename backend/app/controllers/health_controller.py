"""health_controller.py - Respuestas de las rutas de salud del servidor."""
from flask import jsonify

from app.services.health_service import estado_base_datos, estado_servidor


def salud():
    return jsonify(estado_servidor()), 200


def salud_base_datos():
    try:
        return jsonify(estado_base_datos()), 200
    except Exception:
        return jsonify({"estado": "ERROR", "mensaje": "No se pudo consultar la base de datos"}), 500
