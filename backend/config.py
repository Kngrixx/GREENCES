"""
config.py - Configuracion del backend.

Los valores que son secretos o que cambian segun el computador (usuario y clave
de PostgreSQL, clave para firmar los tokens) se leen del archivo .env, que NO se
sube a GitHub. La plantilla que si se sube es .env.example.
"""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    # ---------- Base de datos (PostgreSQL) ----------
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------- Autenticacion con JWT ----------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    # Cuanto dura un token antes de que haya que iniciar sesion otra vez.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_HORAS", "8")))

    # ---------- CORS: desde que paginas se permite llamar a la API ----------
    # El frontend de Angular corre en http://localhost:4200. Se pueden poner
    # varios origenes separados por coma.
    CORS_ALLOWED_ORIGINS = [
        origen.strip()
        for origen in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:4200").split(",")
        if origen.strip()
    ]

    # ---------- Monitoreo ----------
    # El ESP32 envia cada 15 s. Si la ultima lectura tiene mas de 20 s, el
    # sistema se muestra como "sin datos recientes" (apagado o desconectado).
    SEGUNDOS_EN_LINEA = int(os.getenv("SEGUNDOS_EN_LINEA", "20"))
