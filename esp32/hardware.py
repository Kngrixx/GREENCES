"""
hardware.py - Clases que representan el hardware de GreenCES.

Cada clase envuelve un pin del ESP32 y ofrece metodos con nombres claros
(encender, escribir, leer...). Asi el programa principal no tiene que saber
nada de Pin, PWM o ADC: solo usa objetos
"""
import time
from machine import Pin, PWM, ADC


class SalidaDigital:
    """Salida de dos estados: un LED o el rele (a traves del transistor Q1)."""

    def __init__(self, numero_pin, activo_en_alto=True):
        # activo_en_alto=True: un 1 en el pin enciende. Si se usara un modulo que
        # se activa con 0 (como el rele sin Q1), bastaria con pasar False.
        self._activo_en_alto = activo_en_alto
        self._pin = Pin(numero_pin, Pin.OUT)
        self._estado = 0
        self.apagar()                      # todo arranca apagado

    def encender(self):
        self._pin.value(1 if self._activo_en_alto else 0)
        self._estado = 1

    def apagar(self):
        self._pin.value(0 if self._activo_en_alto else 1)
        self._estado = 0

    def toggle(self):
        """Cambia al estado contrario. Se usa para el parpadeo del LED blanco."""
        if self._estado:
            self.apagar()
        else:
            self.encender()

    def estado(self):
        """1 si esta encendida, 0 si esta apagada (es lo que va en el JSON)."""
        return self._estado


class SalidaPWM:
    """Salida con intensidad variable: el LED verde."""

    def __init__(self, numero_pin, frecuencia=1000):
        # A 1000 Hz el pin prende y apaga 1000 veces por segundo; el ojo solo
        # ve el brillo promedio, que depende del porcentaje de tiempo encendido.
        self._pwm = PWM(Pin(numero_pin), freq=frecuencia)
        self._porcentaje = 0
        self.escribir(0)

    def escribir(self, porcentaje):
        """Fija la intensidad entre 0 y 100 %."""
        porcentaje = max(0, min(100, int(porcentaje)))
        # duty_u16 va de 0 a 65535: se escala el porcentaje a ese rango.
        self._pwm.duty_u16(porcentaje * 65535 // 100)
        self._porcentaje = porcentaje

    def porcentaje(self):
        """Intensidad actual en % (es lo que va en el JSON como led_verde_pwm)."""
        return self._porcentaje


class EntradaDigital:
    """Entrada digital: el pulsador. Con PULL_UP, suelto = 1 y presionado = 0."""

    def __init__(self, numero_pin, antirrebote_ms=50):
        self._pin = Pin(numero_pin, Pin.IN, Pin.PULL_UP)
        self._antirrebote_ms = antirrebote_ms
        self._ultimo_valor = self._pin.value()
        self._t_ultimo_cambio = time.ticks_ms()

    def leer(self):
        """Valor crudo del pin: 1 suelto, 0 presionado."""
        return self._pin.value()

    def fue_presionado(self):
        """Devuelve True una sola vez por cada pulsacion.

        Detecta el flanco de bajada (1 -> 0) e ignora los cambios que llegan
        antes de antirrebote_ms desde el ultimo cambio aceptado. Asi el rebote
        mecanico del pulsador no cuenta como varias pulsaciones. No usa
        time.sleep(), entonces no frena el resto del programa.
        """
        valor = self._pin.value()
        ahora = time.ticks_ms()
        if valor != self._ultimo_valor and \
                time.ticks_diff(ahora, self._t_ultimo_cambio) >= self._antirrebote_ms:
            self._ultimo_valor = valor
            self._t_ultimo_cambio = ahora
            return valor == 0              # True solo al presionar, no al soltar
        return False


class SenalAnaloga:
    """Entrada analogica: el YL-69, leido por la salida AO del modulo YL-38."""

    def __init__(self, numero_pin, valor_0, valor_100, muestras=10):
        # valor_0 y valor_100: lecturas del ADC que corresponden a 0 % y a 100 %.
        # En el YL-69 la lectura BAJA cuando hay mas agua, por eso valor_0 > valor_100.
        self._adc = ADC(Pin(numero_pin))
        self._adc.atten(ADC.ATTN_11DB)     # rango de 0 a ~3,1 V
        self._valor_0 = valor_0
        self._valor_100 = valor_100
        self._muestras = muestras

    def leer_valor(self):
        """Lectura cruda del ADC (0 a 4095): promedio de varias muestras para quitar ruido."""
        total = 0
        for _ in range(self._muestras):
            total += self._adc.read()
        return total // self._muestras

    def leer_voltaje(self):
        """Voltaje en el pin, en voltios (con la calibracion interna del ESP32)."""
        return self._adc.read_uv() / 1000000

    def leer_porcentaje(self, valor=None):
        """Convierte la lectura a 0-100 % con una regla de tres y la limita a ese rango.

        Si ya se tiene una lectura (de leer_valor), se puede pasar como valor para
        no leer el ADC otra vez; si no, la funcion hace su propia lectura.
        """
        if valor is None:
            valor = self.leer_valor()
        porcentaje = (valor - self._valor_0) * 100 / (self._valor_100 - self._valor_0)
        return max(0.0, min(100.0, porcentaje))
