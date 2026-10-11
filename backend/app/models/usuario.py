"""
usuario.py - Tabla "usuarios": las personas que pueden entrar a la plataforma.

Los usuarios se crean desde Postman (POST /api/auth/registro). La contrasena
nunca se guarda tal cual: se guarda su hash (ver services/auth_service.py).
"""
from app.common.fechas import ahora_utc
from app.extensions import db


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    identificacion = db.Column(db.String(50), nullable=False, unique=True)
    nombre_completo = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime(timezone=True), nullable=False, default=ahora_utc)
    actualizado_en = db.Column(db.DateTime(timezone=True), nullable=False,
                               default=ahora_utc, onupdate=ahora_utc)
