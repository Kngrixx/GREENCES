"""
reglas.py - Reglas de control de GreenCES (secciones 3 y 4 de la guia).

Son funciones "puras": reciben las mediciones y devuelven que hay que hacer,
sin tocar ningun pin. Por eso se pueden probar en el computador, y el programa
principal queda corto: mide, le pregunta a estas funciones y aplica la respuesta.
"""
import config

# Modos del LED blanco. El numero es tambien el valor que va en el JSON.
BLANCO_APAGADO = 0
BLANCO_FIJO = 1
BLANCO_PARPADEO = 2


def intensidad_led_verde(temperatura):
    """Porcentaje del LED verde segun la temperatura."""
    if temperatura < config.T_LIMITE_BAJO:       # T < 28
        return 30
    if temperatura < config.T_LIMITE_MEDIO:      # 28 <= T < 35
        return 70
    if temperatura < config.T_LIMITE_ALTO:       # 35 <= T < 40
        return 100
    return 0                                     # T >= 40: el verde se apaga, prende el rojo


def led_rojo_encendido(temperatura):
    """El LED rojo solo se enciende con T >= 40 C."""
    return temperatura >= config.T_LIMITE_ALTO


def ventilador_encendido(temperatura, estaba_encendido):
    """Histeresis: enciende con T >= 35 y solo se apaga con T < 32.

    Entre 32 y 35 C conserva el estado que traia. Asi el ventilador no prende
    y apaga a cada rato cuando la temperatura ronda los 35 C.
    """
    if temperatura >= config.T_VENTILADOR_ON:
        return True
    if temperatura < config.T_VENTILADOR_OFF:
        return False
    return estaba_encendido


def modo_led_blanco(humedad_ambiente, humedad_suelo):
    """Modo del LED blanco segun las dos humedades.

    - Al menos una humedad >= 70 %   -> parpadea cada 500 ms
    - Las dos humedades < 30 %       -> encendido fijo
    - Cualquier otro caso            -> apagado
    Si la humedad ambiente no esta disponible (None), solo cuenta la del suelo
    para la regla de parpadeo, y la regla de "fijo" no se puede cumplir.
    """
    ambiente_alta = humedad_ambiente is not None and humedad_ambiente >= config.HUMEDAD_ALTA
    if ambiente_alta or humedad_suelo >= config.HUMEDAD_ALTA:
        return BLANCO_PARPADEO
    if humedad_ambiente is not None and humedad_ambiente < config.HUMEDAD_BAJA \
            and humedad_suelo < config.HUMEDAD_BAJA:
        return BLANCO_FIJO
    return BLANCO_APAGADO
