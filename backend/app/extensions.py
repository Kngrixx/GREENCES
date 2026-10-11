"""
extensions.py - Objetos de las extensiones de Flask.

Se crean aqui, sin aplicacion, y se conectan a ella en create_app() con
init_app(). Asi los modelos y servicios pueden importar "db" sin importar la app
(evita importaciones circulares).
"""
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()       # ORM: las tablas se manejan como clases de Python
migrate = Migrate()     # migraciones: crean y actualizan las tablas en PostgreSQL
jwt = JWTManager()      # crea y verifica los tokens del login
