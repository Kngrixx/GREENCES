"""health_routes.py - Rutas para revisar que el servidor y la base de datos respondan (sin token)."""
from flask import Blueprint

from app.controllers.health_controller import salud, salud_base_datos

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def salud_ruta():
    return salud()


@health_bp.route("/health/db", methods=["GET"])
def salud_base_datos_ruta():
    return salud_base_datos()
