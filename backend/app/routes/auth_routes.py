"""auth_routes.py - Rutas de autenticacion."""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.controllers.auth_controller import login, perfil, registro

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/registro", methods=["POST"])
def registro_ruta():
    return registro()


@auth_bp.route("/auth/login", methods=["POST"])
def login_ruta():
    return login()


@auth_bp.route("/auth/perfil", methods=["GET"])
@jwt_required()
def perfil_ruta():
    return perfil()
