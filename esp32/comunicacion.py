"""
comunicacion.py - Conexion WiFi y envio de los datos al backend (guia, seccion 6).

Dos clases:
  - ConexionWiFi: conecta el ESP32 a la red sin bloquear el programa. Pide la
    conexion y sigue de largo; en cada vuelta del ciclo revisa si ya conecto y,
    si no, lo vuelve a intentar cada cierto tiempo (medido con ticks, sin sleep).
  - ClienteServidor: envia el JSON al backend con una peticion HTTP POST.

La ruta que recibe los datos NO lleva token (guia, NOTA 4): el ESP32 solo envia.
"""
import json
import time
import network

try:
    import requests                 # nombre del modulo en MicroPython 1.20 o mas nuevo
except ImportError:
    import urequests as requests    # nombre en firmwares mas viejos


class ConexionWiFi:
    """El ESP32 en modo estacion (STA): se une a una red WiFi que ya existe."""

    def __init__(self, ssid, clave, reintento_ms=10000):
        self._ssid = ssid
        self._clave = clave
        self._reintento_ms = reintento_ms
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        self._estaba_conectado = False
        self._t_intento = time.ticks_ms()
        if not self._wlan.isconnected():    # tras un reinicio suave puede seguir conectado
            self._intentar()

    def _intentar(self):
        """Pide la conexion y regresa de inmediato: el WiFi se conecta en segundo plano."""
        print("WiFi: conectando a", self._ssid, "...")
        try:
            self._wlan.disconnect()         # cancela un intento anterior que haya quedado a medias
        except OSError:
            pass                            # no habia nada que cancelar
        try:
            self._wlan.connect(self._ssid, self._clave)
        except OSError as error:
            print("WiFi: error al pedir la conexion:", error)
        self._t_intento = time.ticks_ms()

    def _motivo(self):
        """Traduce el estado del WiFi a un mensaje que ayude a encontrar el problema."""
        estado = self._wlan.status()
        if estado == getattr(network, "STAT_WRONG_PASSWORD", None):
            return "clave incorrecta"
        if estado == getattr(network, "STAT_NO_AP_FOUND", None):
            return "no se encuentra la red (revisa el nombre; debe ser de 2,4 GHz)"
        return "estado " + str(estado)

    def actualizar(self):
        """Se llama en cada vuelta del ciclo: avisa los cambios y reintenta si hace falta."""
        conectado = self._wlan.isconnected()
        ahora = time.ticks_ms()
        if conectado != self._estaba_conectado:
            self._estaba_conectado = conectado
            self._t_intento = ahora
            if conectado:
                print("WiFi conectado. IP del ESP32:", self.ip())
            else:
                print("WiFi: se perdio la conexion")
        elif not conectado and time.ticks_diff(ahora, self._t_intento) >= self._reintento_ms:
            print("WiFi: sin conexion ->", self._motivo())
            self._intentar()

    def conectado(self):
        return self._wlan.isconnected()

    def ip(self):
        return self._wlan.ifconfig()[0]


class ClienteServidor:
    """Envia los datos al backend como JSON con una peticion HTTP POST."""

    def __init__(self, url, timeout_s=3):
        self._url = url
        # Tiempo maximo de espera: si el servidor no contesta, el ESP32 no se
        # queda colgado y vuelve a atender el pulsador y los LEDs.
        self._timeout_s = timeout_s

    def url(self):
        return self._url

    def enviar(self, datos):
        """Envia datos (un diccionario). Devuelve el codigo HTTP, o None si no hubo respuesta."""
        respuesta = None
        try:
            respuesta = requests.post(
                self._url,
                data=json.dumps(datos),
                headers={"Content-Type": "application/json"},
                timeout=self._timeout_s,
            )
            return respuesta.status_code
        except Exception as error:          # servidor apagado, IP equivocada, timeout...
            print("POST fallido:", error)
            return None
        finally:
            if respuesta is not None:
                respuesta.close()           # libera el socket (el ESP32 tiene pocos)
