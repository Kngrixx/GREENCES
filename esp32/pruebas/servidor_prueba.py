"""
servidor_prueba.py - Servidor minimo para probar el envio del ESP32 ANTES de tener el backend.

Se ejecuta en el COMPUTADOR (no en la placa), con Python normal y sin instalar nada:

    python esp32/pruebas/servidor_prueba.py

Escucha en el puerto 5000 la misma ruta que tendra el backend Flask
(POST /api/lecturas), imprime cada JSON que llega y cuantos segundos pasaron
desde el anterior (deben ser ~15 s), y responde 201 como lo hara el backend.
Se detiene con Ctrl+C. En el Paso 2 se reemplaza por el backend real.
"""
import json
import socket
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

PUERTO = 5000
RUTA = "/api/lecturas"
CLAVES = ("sistema", "temperatura", "humedad_ambiente", "humedad_suelo",
          "led_verde_pwm", "led_rojo", "led_blanco", "ventilador")


def ip_local():
    """IP de este computador en la red local (la que va en secretos.SERVIDOR)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))      # no envia nada: solo elige la interfaz de red
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class Manejador(BaseHTTPRequestHandler):
    ultimo = None                       # instante del dato anterior, para medir el intervalo

    def _responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_POST(self):
        if self.path != RUTA:
            self._responder(404, {"error": "ruta no encontrada"})
            return
        largo = int(self.headers.get("Content-Length", 0))
        try:
            datos = json.loads(self.rfile.read(largo))
        except ValueError:
            print("Llego algo que no es JSON")
            self._responder(400, {"error": "el cuerpo no es JSON"})
            return
        faltan = [c for c in CLAVES if not isinstance(datos, dict) or c not in datos]
        ahora = time.monotonic()
        intervalo = "" if Manejador.ultimo is None else " (+%.1f s)" % (ahora - Manejador.ultimo)
        Manejador.ultimo = ahora
        hora = datetime.now().strftime("%H:%M:%S")
        print("[%s] %s%s -> %s" % (hora, self.client_address[0], intervalo, json.dumps(datos)))
        if faltan:
            print("   Faltan claves:", ", ".join(faltan))
            self._responder(400, {"error": "faltan claves", "faltan": faltan})
            return
        self._responder(201, {"mensaje": "lectura recibida"})

    def log_message(self, formato, *args):
        pass                            # sin el registro automatico de http.server


if __name__ == "__main__":
    servidor = HTTPServer(("0.0.0.0", PUERTO), Manejador)
    print("Servidor de prueba escuchando en el puerto", PUERTO)
    print('En esp32/secretos.py pon:  SERVIDOR = "http://%s:%d"' % (ip_local(), PUERTO))
    print("Esperando datos del ESP32... (Ctrl+C para salir)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")
