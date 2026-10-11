"""health_service.py - Revisa que el servidor y la base de datos respondan."""
from sqlalchemy import text

from app.extensions import db


def estado_servidor():
    return {"estado": "OK", "servicio": "GreenCES backend"}


def estado_base_datos():
    db.session.execute(text("SELECT 1"))      # consulta minima: si falla, lanza una excepcion
    return {"estado": "OK", "servicio": "PostgreSQL"}
