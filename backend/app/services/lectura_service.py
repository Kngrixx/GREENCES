"""
lectura_service.py - Guardar y consultar las lecturas del ESP32.

Las consultas se hacen con SQLAlchemy; cada funcion explica la consulta SQL que
termina ejecutando PostgreSQL.
"""
import math
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.extensions import db
from app.models.lectura import Lectura

# El ESP32 envia una lectura cada 15 s. El grafico del Dashboard recibe como
# maximo MAX_PUNTOS puntos: en periodos cortos cada lectura es un punto y en
# periodos largos se agrupan en intervalos (ver serie_temperatura).
SEGUNDOS_ENTRE_ENVIOS = 15
MAX_PUNTOS = 300


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


def serie_temperatura(desde, hasta):
    """Puntos (fecha, temperatura, lecturas) del grafico, del mas viejo al mas nuevo.

    desde=None -> todo el historico: el periodo empieza en la primera lectura.

    Si el periodo cabe en MAX_PUNTOS envios (hasta 75 min) cada lectura es un
    punto. Si es mas largo, se divide en intervalos iguales y PostgreSQL agrupa
    las lecturas de cada intervalo (GROUP BY) y devuelve su promedio:

        SELECT AVG(epoca), AVG(temperatura), COUNT(*)
        FROM (SELECT FLOOR(EXTRACT(EPOCH FROM fecha) / intervalo) AS grupo,
                     EXTRACT(EPOCH FROM fecha) AS epoca, temperatura
              FROM lecturas
              WHERE sistema = 'ON' AND temperatura IS NOT NULL AND fecha >= desde) AS t
        GROUP BY grupo ORDER BY grupo

    EXTRACT(EPOCH ...) son los segundos desde 1970: al dividirlos por el
    intervalo y quitar los decimales (FLOOR), todas las lecturas del mismo
    intervalo quedan con el mismo numero de grupo.
    """
    condiciones = [Lectura.sistema == "ON", Lectura.temperatura.is_not(None)]
    if desde is None:
        desde = db.session.execute(select(func.min(Lectura.fecha)).where(*condiciones)).scalar()
        if desde is None:                                  # todavia no hay lecturas
            return {"desde": None, "hasta": hasta, "intervalo_s": SEGUNDOS_ENTRE_ENVIOS, "puntos": []}
    condiciones.append(Lectura.fecha >= desde)

    segundos = max(1.0, (hasta - desde).total_seconds())
    intervalo = max(SEGUNDOS_ENTRE_ENVIOS, math.ceil(segundos / MAX_PUNTOS))

    if intervalo <= SEGUNDOS_ENTRE_ENVIOS:
        # Periodo corto (5 min, 1 h): cada lectura es un punto.
        filas = db.session.execute(
            select(Lectura.fecha, Lectura.temperatura).where(*condiciones).order_by(Lectura.fecha.asc())
        ).all()
        puntos = [(fecha, temperatura, 1) for fecha, temperatura in filas]
    else:
        # Periodo largo (24 h, todo): promedio por intervalo.
        epoca = func.extract("epoch", Lectura.fecha)
        agrupadas = select(
            func.floor(epoca / intervalo).label("grupo"),
            epoca.label("epoca"),
            Lectura.temperatura.label("temperatura"),
        ).where(*condiciones).subquery()
        filas = db.session.execute(
            select(func.avg(agrupadas.c.epoca), func.avg(agrupadas.c.temperatura), func.count())
            .group_by(agrupadas.c.grupo)
            .order_by(agrupadas.c.grupo)
        ).all()
        puntos = [
            (datetime.fromtimestamp(float(epoca_media), timezone.utc), round(float(promedio), 1), cantidad)
            for epoca_media, promedio, cantidad in filas
        ]

    return {"desde": desde, "hasta": hasta, "intervalo_s": intervalo, "puntos": puntos}


def _a_float(valor):
    return None if valor is None else float(valor)
