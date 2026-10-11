"""
lectura_service.py - Guardar y consultar las lecturas del ESP32.

Las consultas se hacen con SQLAlchemy; cada funcion explica la consulta SQL que
termina ejecutando PostgreSQL.
"""
from datetime import timedelta

from sqlalchemy import func, select

from app.common.fechas import ahora_utc
from app.extensions import db
from app.models.lectura import Lectura


def crear_lectura(datos):
    """INSERT INTO lecturas (...) VALUES (...). Los datos ya vienen validados."""
    lectura = Lectura(
        sistema=datos["sistema"],
        temperatura=_a_float(datos["temperatura"]),
        humedad_ambiente=_a_float(datos["humedad_ambiente"]),
        humedad_suelo=float(datos["humedad_suelo"]),
        led_verde_pwm=int(datos["led_verde_pwm"]),
        led_rojo=int(datos["led_rojo"]),
        led_blanco=int(datos["led_blanco"]),
        ventilador=int(datos["ventilador"]),
    )
    db.session.add(lectura)
    db.session.commit()
    return lectura


def obtener_ultima():
    """SELECT * FROM lecturas ORDER BY fecha DESC LIMIT 1  -> la mas reciente (o None)."""
    return db.session.execute(
        select(Lectura).order_by(Lectura.fecha.desc(), Lectura.id.desc()).limit(1)
    ).scalar_one_or_none()


def listar_recientes(limite):
    """Las ultimas 'limite' lecturas, de la mas nueva a la mas vieja."""
    return db.session.execute(
        select(Lectura).order_by(Lectura.fecha.desc(), Lectura.id.desc()).limit(limite)
    ).scalars().all()


def calcular_resumen(desde=None):
    """Maximos y minimos para las tarjetas del Dashboard.

    SELECT MAX(temperatura), MIN(temperatura), ..., COUNT(id)
    FROM lecturas WHERE sistema = 'ON' [AND fecha >= desde]

    Se calculan en la base de datos con MAX y MIN (no trayendo todas las filas a
    Python). MAX y MIN ignoran los null, asi que una lectura sin sensor no
    afecta el resultado. Solo cuentan lecturas con el sistema ENCENDIDO.
    """
    consulta = select(
        func.max(Lectura.temperatura), func.min(Lectura.temperatura),
        func.max(Lectura.humedad_ambiente), func.min(Lectura.humedad_ambiente),
        func.max(Lectura.humedad_suelo), func.min(Lectura.humedad_suelo),
        func.count(Lectura.id),
    ).where(Lectura.sistema == "ON")
    if desde is not None:
        consulta = consulta.where(Lectura.fecha >= desde)

    t_max, t_min, ha_max, ha_min, hs_max, hs_min, total = db.session.execute(consulta).one()
    return {
        "temperatura": {"maximo": t_max, "minimo": t_min},
        "humedad_ambiente": {"maximo": ha_max, "minimo": ha_min},
        "humedad_suelo": {"maximo": hs_max, "minimo": hs_min},
        "total_lecturas": total,
    }


def temperaturas_recientes(minutos):
    """Puntos (fecha, temperatura) de los ultimos 'minutos', del mas viejo al mas nuevo.

    SELECT fecha, temperatura FROM lecturas
    WHERE fecha >= ahora - minutos AND temperatura IS NOT NULL ORDER BY fecha
    """
    desde = ahora_utc() - timedelta(minutes=minutos)
    filas = db.session.execute(
        select(Lectura.fecha, Lectura.temperatura)
        .where(Lectura.fecha >= desde, Lectura.temperatura.is_not(None))
        .order_by(Lectura.fecha.asc())
    ).all()
    return desde, filas


def _a_float(valor):
    return None if valor is None else float(valor)
