"""
lectura_controller.py - Recibe las lecturas del ESP32 y entrega los datos al frontend.
"""
from datetime import timedelta

from flask import current_app, jsonify, request

from app.common.fechas import a_iso, ahora_utc
from app.common.validaciones import validar_lectura
from app.services.lectura_service import (
    calcular_resumen,
    crear_lectura,
    listar_recientes,
    obtener_ultima,
    serie_temperatura,
)

# Periodo mas largo que se acepta en ?minutos= (un ano). Sin el parametro = todo el historico.
MINUTOS_MAXIMO = 60 * 24 * 365


def lectura_a_dict(lectura):
    return {
        "id": lectura.id,
        "sistema": lectura.sistema,
        "temperatura": lectura.temperatura,
        "humedad_ambiente": lectura.humedad_ambiente,
        "humedad_suelo": lectura.humedad_suelo,
        "led_verde_pwm": lectura.led_verde_pwm,
        "led_rojo": lectura.led_rojo,
        "led_blanco": lectura.led_blanco,
        "ventilador": lectura.ventilador,
        "fecha": a_iso(lectura.fecha),
    }


def _entero_entre(nombre, defecto, minimo, maximo):
    """Lee un parametro de la URL (?nombre=valor) como entero y lo limita al rango."""
    valor = request.args.get(nombre, default=defecto, type=int)
    if valor is None:
        return None
    return max(minimo, min(maximo, valor))


def _inicio_del_periodo(ahora):
    """Lee ?minutos=N (5, 60, 1440...) y devuelve (minutos, desde).

    Sin el parametro: (None, None), que significa todo el historico.
    """
    minutos = _entero_entre("minutos", None, 1, MINUTOS_MAXIMO)
    desde = ahora - timedelta(minutes=minutos) if minutos else None
    return minutos, desde


def recibir_lectura():
    """POST /api/lecturas - La usa el ESP32 cada 15 s. Sin token (NOTA 4 de la guia)."""
    datos = request.get_json(silent=True)
    errores = validar_lectura(datos)
    if errores:
        return jsonify({"mensaje": "Lectura inválida", "errores": errores}), 400

    lectura = crear_lectura(datos)
    return jsonify({"mensaje": "Lectura guardada", "lectura": lectura_a_dict(lectura)}), 201


def ultima_lectura():
    """GET /api/lecturas/ultima - Para la seccion Monitoreo (tiempo real)."""
    lectura = obtener_ultima()
    if lectura is None:
        return jsonify({"lectura": None, "en_linea": False, "segundos_desde_ultima": None}), 200

    segundos = (ahora_utc() - lectura.fecha).total_seconds()
    en_linea = lectura.sistema == "ON" and segundos <= current_app.config["SEGUNDOS_EN_LINEA"]
    return jsonify({
        "lectura": lectura_a_dict(lectura),
        "en_linea": en_linea,                     # False: ESP32 apagado o sin conexion
        "segundos_desde_ultima": round(segundos, 1),
    }), 200


def historial():
    """GET /api/lecturas?limite=20 - Ultimas lecturas guardadas (maximo 500)."""
    limite = _entero_entre("limite", 20, 1, 500)
    lecturas = listar_recientes(limite)
    return jsonify({"total": len(lecturas), "lecturas": [lectura_a_dict(l) for l in lecturas]}), 200


def resumen():
    """GET /api/lecturas/resumen[?minutos=5] - Maximos y minimos para las tarjetas del Dashboard.

    ?minutos=5, 60 o 1440 limita el calculo a ese periodo. Sin el parametro se
    calcula sobre todo el historico.
    """
    minutos, desde = _inicio_del_periodo(ahora_utc())
    datos = calcular_resumen(desde)
    datos["minutos"] = minutos
    datos["desde"] = a_iso(desde)
    return jsonify(datos), 200


def temperatura_reciente():
    """GET /api/lecturas/temperatura[?minutos=5] - Puntos del grafico de linea del Dashboard.

    Con ?minutos=5 (lo que pide la guia) cada lectura es un punto. En periodos
    largos (24 h o todo el historico) el servicio agrupa las lecturas en
    intervalos y devuelve el promedio de cada uno, para no mandar miles de puntos.
    """
    ahora = ahora_utc()
    minutos, desde = _inicio_del_periodo(ahora)
    serie = serie_temperatura(desde, ahora)
    return jsonify({
        "minutos": minutos,                       # null = todo el historico
        "desde": a_iso(serie["desde"]),           # inicio del periodo (todo: la primera lectura)
        "hasta": a_iso(serie["hasta"]),           # hora del servidor al responder
        "intervalo_s": serie["intervalo_s"],      # 15 = cada punto es un envio; mas = promedio
        "puntos": [
            {"fecha": a_iso(fecha), "temperatura": temperatura, "lecturas": cantidad}
            for fecha, temperatura, cantidad in serie["puntos"]
        ],
    }), 200
