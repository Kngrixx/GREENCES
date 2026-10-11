"""
app/__init__.py - Fabrica de la aplicacion (create_app).

Arma el backend por capas:
    routes      -> definen las URL y que rutas piden token
    controllers -> leen la peticion, validan y arman la respuesta JSON
    services    -> logica y consultas a la base de datos
    models      -> tablas de PostgreSQL como clases (SQLAlchemy)
    common      -> utilidades compartidas (validaciones, fechas)
"""
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from app.extensions import db, migrate, jwt
from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.lectura_routes import lectura_bp


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.json.sort_keys = False      # respeta el orden de las claves (como el JSON del ESP32)
    _verificar_configuracion(app)

    # CORS: el navegador solo deja que el frontend (otro origen) llame a /api/*
    # si el backend lo autoriza explicitamente.
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ALLOWED_ORIGINS"]}})

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    _respuestas_de_token()

    from app import models  # noqa: F401  (registra los modelos para las migraciones)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(lectura_bp, url_prefix="/api")

    _errores_en_json(app)
    return app


def _verificar_configuracion(app):
    """Falla con un mensaje claro si falta algo en el archivo .env."""
    faltan = [clave for clave in ("SQLALCHEMY_DATABASE_URI", "JWT_SECRET_KEY") if not app.config.get(clave)]
    if faltan:
        nombres = {"SQLALCHEMY_DATABASE_URI": "DATABASE_URL", "JWT_SECRET_KEY": "JWT_SECRET_KEY"}
        raise RuntimeError(
            "Falta configurar en backend/.env: " + ", ".join(nombres[c] for c in faltan)
            + " (copia .env.example como .env y llena los datos)"
        )


def _respuestas_de_token():
    """Mensajes en espanol cuando una ruta protegida recibe un token malo o ninguno."""

    @jwt.unauthorized_loader
    def sin_token(_motivo):
        return jsonify({"mensaje": "Falta el token. Inicia sesión y envía el encabezado "
                                   "Authorization: Bearer <token>."}), 401

    @jwt.expired_token_loader
    def token_vencido(_encabezado, _contenido):
        return jsonify({"mensaje": "El token venció. Inicia sesión de nuevo."}), 401

    @jwt.invalid_token_loader
    def token_invalido(_motivo):
        return jsonify({"mensaje": "Token inválido."}), 401


def _errores_en_json(app):
    """Respuestas JSON (y no paginas HTML) para rutas que no existen o metodos no permitidos."""

    @app.errorhandler(404)
    def no_encontrado(_error):
        return jsonify({"mensaje": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def metodo_no_permitido(_error):
        return jsonify({"mensaje": "Método no permitido en esta ruta"}), 405
