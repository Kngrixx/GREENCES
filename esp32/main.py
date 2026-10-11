"""
main.py - Programa principal de GreenCES en el ESP32.

Funcionamiento (guia, secciones 2 a 7):
  - Al encender o reiniciar queda APAGADO: sin mediciones ni envios, valores en 0,
    LEDs y ventilador apagados.
  - Cada pulsacion alterna entre APAGADO y ENCENDIDO (con antirrebote).
  - ENCENDIDO: mide los sensores, aplica las reglas de control, muestra el JSON
    en consola cada 2 s y lo envia al backend por WiFi cada 15 s.

Todos los tiempos se manejan con time.ticks_ms() y time.ticks_diff(): no hay
time.sleep(), asi el ciclo nunca se detiene y el pulsador siempre responde.

Para que arranque solo al conectar la placa, este archivo se sube a la placa con
el nombre main.py (MicroPython ejecuta main.py despues de cada reinicio).
"""
import json
import time
from collections import OrderedDict
from machine import I2C, Pin

import config
import reglas
from hardware import SalidaDigital, SalidaPWM, EntradaDigital, SenalAnaloga
from htu21d import HTU21D
from comunicacion import ConexionWiFi, ClienteServidor

try:
    import secretos         # WiFi e IP del servidor (archivo que no se sube a GitHub)
except ImportError:
    secretos = None


def poner(salida, encendida):
    """Enciende o apaga una SalidaDigital segun un valor True/False."""
    if encendida:
        salida.encender()
    else:
        salida.apagar()


class GreenCES:
    """El sistema completo: hardware + estado + reglas + comunicacion."""

    def __init__(self):
        # ---------- hardware ----------
        self.led_verde = SalidaPWM(config.PIN_LED_VERDE)
        self.led_rojo = SalidaDigital(config.PIN_LED_ROJO)
        self.led_blanco = SalidaDigital(config.PIN_LED_BLANCO)
        self.ventilador = SalidaDigital(config.PIN_RELE)          # rele por Q1
        self.pulsador = EntradaDigital(config.PIN_PULSADOR, config.ANTIRREBOTE_MS)
        self.suelo = SenalAnaloga(config.PIN_SUELO, config.SUELO_SECO, config.SUELO_AGUA)
        i2c = I2C(0, sda=Pin(config.PIN_SDA), scl=Pin(config.PIN_SCL), freq=100000)
        self.ambiente = HTU21D(i2c, config.LECTURA_SENSORES_MS)

        # ---------- comunicacion ----------
        # El WiFi se conecta desde el arranque para estar listo, pero los datos
        # solo se envian con el sistema ENCENDIDO.
        if secretos is not None:
            self.wifi = ConexionWiFi(secretos.WIFI_SSID, secretos.WIFI_CLAVE,
                                     config.WIFI_REINTENTO_MS)
            self.servidor = ClienteServidor(secretos.SERVIDOR + config.RUTA_LECTURAS,
                                            config.HTTP_TIMEOUT_S)
        else:
            self.wifi = None
            self.servidor = None

        # ---------- estado ----------
        self.encendido = False
        self.modo_blanco = reglas.BLANCO_APAGADO
        self.temperatura = 0
        self.humedad_ambiente = 0
        self.humedad_suelo = 0

        # ---------- temporizadores (instantes en ms, de time.ticks_ms) ----------
        ahora = time.ticks_ms()
        self.t_lectura = ahora
        self.t_parpadeo = ahora
        self.t_envio = ahora
        self.t_inicio_sim = ahora

        self.apagar_todo()

    # ===================== encendido / apagado =====================
    def alternar_sistema(self):
        """Lo que pasa con cada pulsacion: ENCENDIDO <-> APAGADO."""
        self.encendido = not self.encendido
        ahora = time.ticks_ms()
        if self.encendido:
            print("Sistema ENCENDIDO")
            self.ambiente.reiniciar()               # mide de una vez, sin datos viejos
            self.t_inicio_sim = ahora
            # La primera lectura y el primer envio se hacen PRIMERA_LECTURA_MS despues
            # de encender (tiempo para que el HTU21D termine de medir). Para lograrlo,
            # los temporizadores se ponen "en el pasado": como si la ultima lectura
            # hubiera sido hace casi 2 s y el ultimo envio hace casi 15 s.
            primera = time.ticks_add(ahora, config.PRIMERA_LECTURA_MS)
            self.t_lectura = time.ticks_add(primera, -config.LECTURA_SENSORES_MS)
            self.t_envio = time.ticks_add(primera, -config.ENVIO_MS)
        else:
            print("Sistema APAGADO")
            self.apagar_todo()
            self.mostrar_json()

    def apagar_todo(self):
        """Estado APAGADO de la guia: valores en 0, LEDs y ventilador apagados."""
        self.led_verde.escribir(0)
        self.led_rojo.apagar()
        self.led_blanco.apagar()
        self.ventilador.apagar()
        self.modo_blanco = reglas.BLANCO_APAGADO
        self.temperatura = 0
        self.humedad_ambiente = 0
        self.humedad_suelo = 0

    # ===================== mediciones =====================
    def medir(self):
        """Actualiza temperatura, humedad ambiente y humedad del suelo."""
        self.humedad_suelo = round(self.suelo.leer_porcentaje(), 1)
        if config.SIMULAR_AMBIENTE:
            self.temperatura, self.humedad_ambiente = self.ambiente_simulado()
        else:
            # Si el HTU21D no responde, estos valores llegan como None (null en el JSON).
            self.temperatura = self.ambiente.leer_temperatura()
            self.humedad_ambiente = self.ambiente.leer_humedad()

    def ambiente_simulado(self):
        """Rampa que sube y baja (forma de triangulo) para probar las reglas sin el HTU21D."""
        periodo = config.SIM_PERIODO_MS
        fase = time.ticks_diff(time.ticks_ms(), self.t_inicio_sim) % periodo
        mitad = periodo / 2
        x = fase / mitad if fase < mitad else (periodo - fase) / mitad   # va de 0 a 1 y vuelve a 0
        t = config.SIM_T_MIN + (config.SIM_T_MAX - config.SIM_T_MIN) * x
        h = config.SIM_H_MIN + (config.SIM_H_MAX - config.SIM_H_MIN) * x
        return round(t, 1), round(h, 1)

    # ===================== reglas de control =====================
    def aplicar_reglas(self):
        t = self.temperatura
        if t is None:
            # Sin dato de temperatura no se puede decidir: lo que depende de T queda apagado.
            self.led_verde.escribir(0)
            self.led_rojo.apagar()
            self.ventilador.apagar()
        else:
            self.led_verde.escribir(reglas.intensidad_led_verde(t))
            poner(self.led_rojo, reglas.led_rojo_encendido(t))
            poner(self.ventilador, reglas.ventilador_encendido(t, self.ventilador.estado()))

        modo = reglas.modo_led_blanco(self.humedad_ambiente, self.humedad_suelo)
        if modo != self.modo_blanco:
            self.modo_blanco = modo
            if modo == reglas.BLANCO_FIJO:
                self.led_blanco.encender()
            elif modo == reglas.BLANCO_APAGADO:
                self.led_blanco.apagar()
            else:
                self.t_parpadeo = time.ticks_ms()   # el parpadeo lo maneja actualizar_parpadeo()

    def actualizar_parpadeo(self):
        """Si el LED blanco esta en modo parpadeo, lo cambia cada 500 ms."""
        ahora = time.ticks_ms()
        if self.modo_blanco == reglas.BLANCO_PARPADEO and \
                time.ticks_diff(ahora, self.t_parpadeo) >= config.PARPADEO_MS:
            self.led_blanco.toggle()
            self.t_parpadeo = ahora

    # ===================== JSON y envio =====================
    def datos(self):
        """Los datos en el orden de la guia (OrderedDict conserva el orden al pasarlos a JSON)."""
        d = OrderedDict()
        d["sistema"] = "ON" if self.encendido else "OFF"
        d["temperatura"] = self.temperatura
        d["humedad_ambiente"] = self.humedad_ambiente
        d["humedad_suelo"] = self.humedad_suelo
        d["led_verde_pwm"] = self.led_verde.porcentaje()
        d["led_rojo"] = self.led_rojo.estado()
        d["led_blanco"] = self.modo_blanco
        d["ventilador"] = self.ventilador.estado()
        return d

    def mostrar_json(self):
        print(json.dumps(self.datos()))

    def enviar(self):
        """Envia el JSON al backend (se llama cada 15 s, solo con el sistema ENCENDIDO)."""
        if self.servidor is None:
            print("Envio omitido: falta secretos.py")
            return
        if not self.wifi.conectado():
            print("Envio omitido: sin WiFi")
            return
        codigo = self.servidor.enviar(self.datos())
        if codigo is None:
            return                                   # el error ya lo imprimio ClienteServidor
        if 200 <= codigo < 300:
            print("POST ->", codigo, "OK")
        else:
            print("POST ->", codigo, "(el servidor rechazo los datos)")

    # ===================== ciclo principal =====================
    def ciclo(self):
        """Una vuelta del ciclo principal. Nunca se queda esperando."""
        if self.wifi is not None:
            self.wifi.actualizar()                  # conecta o reconecta en segundo plano

        if self.pulsador.fue_presionado():
            self.alternar_sistema()

        if not self.encendido:
            return                                  # APAGADO: no mide ni envia

        if not config.SIMULAR_AMBIENTE:
            self.ambiente.actualizar()              # el HTU21D avanza su medicion por etapas

        ahora = time.ticks_ms()
        if time.ticks_diff(ahora, self.t_lectura) >= config.LECTURA_SENSORES_MS:
            self.t_lectura = ahora
            self.medir()
            self.aplicar_reglas()
            self.mostrar_json()

        self.actualizar_parpadeo()

        if time.ticks_diff(ahora, self.t_envio) >= config.ENVIO_MS:
            self.t_envio = ahora
            self.enviar()


def main():
    sistema = GreenCES()
    print("GreenCES listo. Sistema APAGADO: presiona el pulsador para encender.")
    if config.SIMULAR_AMBIENTE:
        print("AVISO: temperatura y humedad ambiente SIMULADAS (config.SIMULAR_AMBIENTE = True)")
    elif sistema.ambiente.disponible:
        print("HTU21D detectado en 0x40")
    else:
        print("AVISO: el HTU21D no responde; temperatura y humedad ambiente iran en null")
    if sistema.servidor is None:
        print("AVISO: falta secretos.py; el programa funciona pero no envia datos")
    else:
        print("Los datos se enviaran a", sistema.servidor.url())
    try:
        while True:
            sistema.ciclo()
    finally:
        sistema.apagar_todo()       # si se detiene con Ctrl+C, todo queda apagado


if __name__ == "__main__":
    main()
