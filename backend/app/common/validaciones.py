"""
validaciones.py - Revisa que el JSON del ESP32 este completo y con valores validos
antes de guardarlo (rubrica: "endpoint de recepcion POST funcional y validado").

validar_lectura() devuelve una LISTA de errores: vacia si todo esta bien. Asi el
ESP32 (o Postman) recibe todos los problemas de una vez, no solo el primero.
"""

# Mismas claves y mismo orden que el JSON que imprime y envia el ESP32.
CAMPOS_LECTURA = (
    "sistema", "temperatura", "humedad_ambiente", "humedad_suelo",
    "led_verde_pwm", "led_rojo", "led_blanco", "ventilador",
)


def _es_numero(valor):
    # En Python True/False tambien son int; aqui no se aceptan como numeros.
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _validar_numero(errores, datos, campo, minimo, maximo, permite_nulo=False):
    valor = datos[campo]
    if valor is None:
        if not permite_nulo:
            errores.append(f"{campo} no puede ser null")
        return
    if not _es_numero(valor):
        errores.append(f"{campo} debe ser un número")
    elif not minimo <= valor <= maximo:
        errores.append(f"{campo} debe estar entre {minimo} y {maximo}")


def _validar_opcion(errores, datos, campo, opciones):
    valor = datos[campo]
    if not _es_numero(valor) or valor not in opciones:
        errores.append(f"{campo} debe ser uno de: {', '.join(str(o) for o in opciones)}")


def validar_lectura(datos):
    """Revisa una lectura del ESP32. Devuelve la lista de errores (vacia = valida)."""
    if not isinstance(datos, dict):
        return ["El cuerpo debe ser un objeto JSON (Content-Type: application/json)"]

    faltan = [campo for campo in CAMPOS_LECTURA if campo not in datos]
    if faltan:
        return ["Faltan campos: " + ", ".join(faltan)]

    errores = []
    if datos["sistema"] not in ("ON", "OFF"):
        errores.append("sistema debe ser 'ON' u 'OFF'")
    # Rango de medicion del HTU21D: -40 a 125 C. Puede venir null si el sensor no responde.
    _validar_numero(errores, datos, "temperatura", -40, 125, permite_nulo=True)
    _validar_numero(errores, datos, "humedad_ambiente", 0, 100, permite_nulo=True)
    _validar_numero(errores, datos, "humedad_suelo", 0, 100)
    _validar_opcion(errores, datos, "led_verde_pwm", (0, 30, 70, 100))
    _validar_opcion(errores, datos, "led_rojo", (0, 1))
    _validar_opcion(errores, datos, "led_blanco", (0, 1, 2))
    _validar_opcion(errores, datos, "ventilador", (0, 1))
    return errores
