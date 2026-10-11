"""
fechas.py - Utilidades de fecha y hora.

Todas las fechas se guardan en UTC (con zona horaria). El frontend las convierte
a la hora de Colombia al mostrarlas.
"""
from datetime import datetime, timezone


def ahora_utc():
    """Fecha y hora actual en UTC."""
    return datetime.now(timezone.utc)


def a_iso(fecha):
    """Convierte una fecha a texto ISO 8601 (ej. 2026-10-10T21:30:05.123456+00:00)."""
    return fecha.isoformat() if fecha else None
