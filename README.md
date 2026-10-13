# GreenCES — Monitoreo y ventilación inteligente

GreenCES es un invernadero inteligente para una zona de almacenamiento de material biológico. Un ESP32 mide la temperatura, la humedad ambiente y la humedad del suelo, decide qué LEDs encender y cuándo prender el ventilador, y envía los datos a un servidor. Una página web los muestra en tiempo real y guarda el historial.

> Examen 3 — Integración de Programación 2 y Algoritmos y Estructura de Datos (CES, 2026-2).
> Autor: Alejandro Chaux.

## Cómo funciona

```
 ┌──────────────────────┐   POST JSON cada 15 s    ┌──────────────────────────┐   GET con token   ┌──────────────────────┐
 │ ESP32 + sensores     │ ───────────────────────▶ │ Backend Flask            │ ◀──────────────── │ Frontend Angular     │
 │ (MicroPython)        │      (sin token)         │ + PostgreSQL             │                   │ Home · Monitoreo ·   │
 │ Computador 1 (USB)   │                          │ Computador 2             │                   │ Dashboard            │
 └──────────────────────┘                          └──────────────────────────┘                   └──────────────────────┘
```

1. El **ESP32** lee los sensores, aplica las reglas de control, imprime el JSON en consola y lo envía al backend.
2. El **backend** valida el JSON, lo guarda en la base de datos y lo entrega a quien tenga un token válido.
3. El **frontend** pide los datos al backend y los muestra.

## Estructura del repositorio

| Carpeta | Qué contiene | Tecnología |
| --- | --- | --- |
| `esp32/` | Programa del microcontrolador: sensores, reglas de control y envío por WiFi | MicroPython |
| `backend/` | API que recibe, guarda y entrega las lecturas, con login por token | Flask, SQLAlchemy, PostgreSQL, JWT |
| `frontend/` | Página web con Home, Monitoreo y Dashboard | Angular |

## Hardware y pines

Placa: Heltec WiFi LoRa 32 V3 (ESP32-S3).

| Componente | Pin | Clase | Notas |
| --- | --- | --- | --- |
| Pulsador | GPIO2 | `EntradaDigital` | `PULL_UP`: presionado = 0 |
| LED verde | GPIO6 | `SalidaPWM` | Intensidad 0, 30, 70 o 100 % |
| LED rojo | GPIO7 | `SalidaDigital` | Encendido solo si T ≥ 40 °C |
| LED blanco | GPIO5 | `SalidaDigital` | Fijo o parpadeando cada 500 ms |
| Relé del ventilador | GPIO3 | `SalidaDigital` | A través del transistor Q1 (2N2222A): 1 = ventilador encendido |
| YL-69 (salida AO) | GPIO4 | `SenalAnaloga` | ADC de 12 bits (0–4095) |
| HTU21D SDA / SCL | GPIO41 / GPIO42 | `HTU21D` | Bus I2C, dirección 0x40 |

¿Por qué estos pines?

- **GPIO1–GPIO7** son los pines libres que marca el diagrama de clase de la Heltec V3. Los demás los ocupan la pantalla OLED (17/18), el módulo LoRa (8–14) y el USB (19/20).
- **Los tres LEDs van en GPIO5, GPIO6 y GPIO7**, que son pines vecinos de la placa. Así quedan juntos en la protoboard.
- **El YL-69 va en GPIO4** porque ese pin pertenece al ADC1. El ADC2 deja de funcionar cuando el WiFi está encendido.
- **El HTU21D usa 41/42** porque 17/18 ya los usa la pantalla.

El módulo de relé se activa con nivel bajo y es de 5 V (transistor PNP 2TY), así que los 3,3 V del ESP32 no lo apagan del todo. Por eso el GPIO3 lo maneja a través de un transistor NPN 2N2222A con 1 kΩ en la base: GPIO3 = 1 → Q1 conduce → IN a 0 V → relé encendido.

Alimentación: los sensores van a 3.3 V. Si el YL-69 se conecta a 5 V, su salida puede superar los 3.3 V que soporta la entrada analógica. El relé va a 5 V, con GND común con el ESP32.

El HTU21D del montaje está dañado (al módulo GY-21 le falta el regulador). El programa tiene un modo simulado y un modo real que se cambian con una línea de `esp32/config.py`; ver [`esp32/README.md`](esp32/README.md#modo-simulado-y-modo-real).

## Datos que envía el ESP32 (JSON)

El mismo objeto se imprime en consola cada 2 s y se envía al backend cada 15 s con `POST /api/lecturas` (ruta sin token, como pide la NOTA 4 de la guía). Los nombres de las claves deben ser idénticos en el ESP32, el backend y el frontend.

```json
{
  "sistema": "ON",
  "temperatura": 36.4,
  "humedad_ambiente": 54.2,
  "humedad_suelo": 27.5,
  "led_verde_pwm": 100,
  "led_rojo": 0,
  "led_blanco": 0,
  "ventilador": 1
}
```

| Clave | Valores | Significado |
| --- | --- | --- |
| `sistema` | `"ON"` / `"OFF"` | Estado que controla el pulsador |
| `temperatura` | °C o `null` | HTU21D (`null` si el sensor no responde) |
| `humedad_ambiente` | 0–100 % o `null` | HTU21D (`null` si el sensor no responde) |
| `humedad_suelo` | 0–100 % | YL-69 calibrado (seco = 0 %, sumergido = 100 %) |
| `led_verde_pwm` | 0, 30, 70, 100 | Intensidad del LED verde en % |
| `led_rojo` | 0 / 1 | Apagado / encendido |
| `led_blanco` | 0 / 1 / 2 | Apagado / fijo / parpadeando (el 2 es propuesta propia, por confirmar con el profe) |
| `ventilador` | 0 / 1 | Relé apagado / encendido |

## Reglas de control

Solo se aplican con el sistema **ENCENDIDO**. Al arrancar, el sistema queda **APAGADO**: sin mediciones, sin envíos, valores en 0, LEDs y ventilador apagados. Cada pulsación alterna entre los dos estados, con antirrebote.

| Temperatura | LED verde | LED rojo | Ventilador |
| --- | --- | --- | --- |
| T < 28 °C | 30 % | apagado | según la histéresis (abajo) |
| 28 ≤ T < 35 °C | 70 % | apagado | según la histéresis |
| 35 ≤ T < 40 °C | 100 % | apagado | encendido |
| T ≥ 40 °C | apagado | encendido | encendido |

**Ventilador con histéresis:** enciende cuando T ≥ 35 °C y solo se apaga cuando T < 32 °C. Entre 32 y 35 °C conserva el estado que traía. Así no prende y apaga a cada rato cuando la temperatura ronda los 35 °C.

| Humedades | LED blanco |
| --- | --- |
| Ambiente < 30 % **Y** suelo < 30 % | Encendido fijo |
| Ambiente ≥ 70 % **O** suelo ≥ 70 % | Parpadeando cada 500 ms |
| Cualquier otro caso | Apagado |

Los tiempos (parpadeo de 500 ms y envío cada 15 s) se miden con `time.ticks_ms()` y `time.ticks_diff()`, nunca con `time.sleep()`. Así el programa sigue leyendo sensores y el pulsador mientras espera.

## Cómo ejecutar

### ESP32

1. Copiar `esp32/pruebas/secretos_ejemplo.py` como `esp32/secretos.py` y llenar la red WiFi (2,4 GHz) y la IP del computador que corre el backend.
2. Con Thonny, subir a la placa `main.py`, `config.py`, `hardware.py`, `htu21d.py`, `reglas.py`, `comunicacion.py` y `secretos.py`.
3. Reiniciar la placa: arranca APAGADA; el pulsador la enciende y la apaga.

Para probar el envío antes de tener el backend: `python esp32/pruebas/servidor_prueba.py` en el computador que recibe. Más detalles en [`esp32/README.md`](esp32/README.md).

### Backend

1. Crear la base de datos `greences` en pgAdmin.
2. En `backend/`: `python -m venv .venv`, `.venv\Scripts\activate` y `pip install -r requirements.txt`.
3. Copiar `backend/.env.example` como `backend/.env` y poner la contraseña de PostgreSQL.
4. `flask db upgrade` (crea las tablas) y `python run.py` (servidor en el puerto 5000).
5. Crear el usuario desde Postman con la colección `backend/postman/GreenCES.postman_collection.json`.

Más detalles y la lista de endpoints en [`backend/README.md`](backend/README.md).

### Frontend

Con el backend corriendo:

```
cd frontend
npm install
ng serve -o
```

Se abre en `http://localhost:4200`. Home es pública; Monitoreo y Dashboard piden iniciar sesión con un usuario creado desde Postman. Más detalles en [`frontend/README.md`](frontend/README.md).

## Avance

- [x] Paso 0 — Estructura del repositorio
- [x] Paso 1 — ESP32: clases de hardware, reglas de control, JSON, WiFi y envío
- [x] Paso 2 — Backend: base de datos, modelos, login con JWT y endpoints
- [x] Paso 3 — Frontend: login, Home, Monitoreo y Dashboard
- [ ] Paso 4 — Prueba en dos computadores y entrega
