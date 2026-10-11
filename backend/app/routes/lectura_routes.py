"""
lectura_routes.py - Rutas de las lecturas del ESP32.

Solo la ruta que RECIBE los datos del ESP32 queda sin token (NOTA 4 de la guia).
Las que entregan informacion al frontend llevan @jwt_required(): sin un token
valido responden 401.
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.lectura_controller import (
    historial,
    recibir_lectura,
    resumen,
    temperatura_reciente,
    ultima_lectura,
)

lectura_bp = Blueprint("lecturas", __name__)


@lectura_bp.route("/lecturas", methods=["POST"])
def recibir_lectura_ruta():                 # ESP32 -> backend (sin token)
    return recibir_lectura()


@lectura_bp.route("/lecturas", methods=["GET"])
@jwt_required()
def historial_ruta():
    return historial()


@lectura_bp.route("/lecturas/ultima", methods=["GET"])
@jwt_required()
def ultima_lectura_ruta():                  # Monitoreo
    return ultima_lectura()


@lectura_bp.route("/lecturas/resumen", methods=["GET"])
@jwt_required()
def resumen_ruta():                         # Dashboard: tarjetas de maximos y minimos
    return resumen()


@lectura_bp.route("/lecturas/temperatura", methods=["GET"])
@jwt_required()
def temperatura_reciente_ruta():            # Dashboard: grafico de los ultimos 5 minutos
    return temperatura_reciente()
