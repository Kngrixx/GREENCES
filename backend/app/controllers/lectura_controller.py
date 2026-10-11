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
    temperaturas_recientes,
)


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
    """GET /api/lecturas/resumen[?horas=24] - Maximos y minimos para las tarjetas del Dashboard.

    Sin ?horas se calcula sobre todo el historico.
    """
    horas = _entero_entre("horas", None, 1, 24 * 365)
    desde = ahora_utc() - timedelta(hours=horas) if horas else None
    datos = calcular_resumen(desde)
    datos["desde"] = a_iso(desde)
    return jsonify(datos), 200


def temperatura_reciente():
    """GET /api/lecturas/temperatura?minutos=5 - Puntos del grafico de linea del Dashboard."""
    minutos = _entero_entre("minutos", 5, 1, 60)
    desde, filas = temperaturas_recientes(minutos)
    return jsonify({
        "minutos": minutos,
        "desde": a_iso(desde),
        "puntos": [{"fecha": a_iso(fecha), "temperatura": temperatura} for fecha, temperatura in filas],
    }), 200
