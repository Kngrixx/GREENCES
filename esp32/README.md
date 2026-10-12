# esp32/

Programa en MicroPython para la Heltec WiFi LoRa 32 V3 (ESP32-S3). Lee los sensores, aplica las reglas de control, imprime el JSON en consola cada 2 s y lo envía al backend por WiFi cada 15 s, solo con el sistema ENCENDIDO.

## Archivos

| Archivo | Va a la placa | Qué hace |
| --- | --- | --- |
| `main.py` | Sí | Programa principal: clase `GreenCES` con el estado ON/OFF, el ciclo sin `sleep`, el JSON y el envío. |
| `config.py` | Sí | Pines, calibración del YL-69, umbrales de las reglas, tiempos, ruta del backend y modo simulado o real del HTU21D. |
| `hardware.py` | Sí | Clases del curso: `SalidaDigital`, `SalidaPWM`, `EntradaDigital`, `SenalAnaloga`. |
| `htu21d.py` | Sí | Clase `HTU21D`: mide por etapas (sin bloquear) y verifica el CRC. |
| `reglas.py` | Sí | Reglas de control como funciones puras (LED verde, LED rojo, ventilador con histéresis, LED blanco). |
| `comunicacion.py` | Sí | `ConexionWiFi` (conexión y reconexión sin bloquear) y `ClienteServidor` (POST del JSON). |
| `secretos.py` | Sí | Red WiFi, clave e IP del servidor. **No se sube a GitHub** (está en `.gitignore`). |
| `secretos_ejemplo.py` | No | Plantilla de `secretos.py` (esta sí va al repositorio). |
| `servidor_prueba.py` | No | Se ejecuta en el PC: recibe los POST para probar el envío antes de tener el backend. |
| `prueba_circuito.py` | No | Menú para probar cada componente del montaje por separado. |
| `prueba_clases.py` | No | Prueba de 20 s de las clases de `hardware.py`. |
| `circuito/` | No | Esquema y montaje en la protoboard. |

## Puesta en marcha

1. Llenar `secretos.py` con la red WiFi (2,4 GHz) y la IP del computador que recibe los datos (`ipconfig` → Dirección IPv4). El ESP32 y ese computador deben estar en la misma red.
2. En Thonny, con la placa conectada, subir a la placa (clic derecho → **Subir a /**): `main.py`, `config.py`, `hardware.py`, `htu21d.py`, `reglas.py`, `comunicacion.py` y `secretos.py`.
3. Reiniciar la placa (botón RST, o **Ctrl+D** en la consola de Thonny). `main.py` arranca solo y el sistema queda APAGADO.
4. Presionar el pulsador para encender y otra vez para apagar.

## Probar el envío sin el backend

En el computador que recibe (PowerShell, en la carpeta del proyecto):

```
python esp32/servidor_prueba.py
```

El servidor muestra la IP que va en `secretos.SERVIDOR` e imprime cada JSON que llega con los segundos transcurridos desde el anterior (deben ser unos 15 s). La primera vez, Windows pregunta si permite el acceso a Python en la red: aceptar para **redes privadas**.

## Datos que envía

`POST {SERVIDOR}/api/lecturas` con `Content-Type: application/json` y el mismo JSON que se imprime en consola (ver el README principal). Esta ruta no lleva token (NOTA 4 de la guía). Si el HTU21D no responde, `temperatura` y `humedad_ambiente` van en `null`.

## Modo simulado y modo real

El HTU21D del montaje (módulo GY-21) está dañado: le falta el regulador. Por eso `config.py` tiene un interruptor:

| `SIMULAR_AMBIENTE` | Temperatura y humedad ambiente | Para qué |
| --- | --- | --- |
| `True` (actual) | Rampa simulada: 24 → 42 °C y 20 → 80 % en 30 s, y de vuelta en otros 30 s | Mostrar todas las reglas de control sin el sensor |
| `False` | HTU21D real por I2C (dirección 0x40) | Funcionamiento con un sensor que sirva |

El resto del programa es igual en los dos modos, y la humedad del suelo (YL-69) siempre es real.

Para pasar al modo real:

1. Conectar el sensor con la placa desconectada (VIN a 3.3 V, GND, SDA a GPIO41, SCL a GPIO42).
2. Poner `SIMULAR_AMBIENTE = False` en `config.py` y subirlo a la placa.
3. Reiniciar (Ctrl+D). La consola debe mostrar `HTU21D detectado en 0x40`.

Si el sensor falla un momento (un cable flojo) o se conecta con el programa corriendo, la clase `HTU21D` lo vuelve a buscar cada 2 s y retoma las lecturas sola.
