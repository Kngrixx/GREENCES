"""
config.py - Configuracion del hardware y de las reglas de control de GreenCES.

Todo lo que depende del montaje (pines) o de una calibracion (valores del YL-69)
esta aqui, en un solo lugar. Las clases y el programa principal solo importan
estos nombres: si algo cambia en la protoboard, se cambia en este archivo.
"""

# ---------------- Pines (ver README y esp32/circuito/) ----------------
PIN_PULSADOR = 2       # a GND, con PULL_UP interno: suelto = 1, presionado = 0
PIN_LED_VERDE = 6      # PWM
PIN_LED_ROJO = 7
PIN_LED_BLANCO = 5
PIN_RELE = 3           # va a la base de Q1 (2N2222A) por 1 kOhm: 1 = ventilador encendido
PIN_SUELO = 4          # AO del YL-38 (ADC1_CH3)
PIN_SDA = 41           # bus I2C del HTU21D
PIN_SCL = 42

# ---------------- Calibracion del YL-69 (medida el 2026-10-10) ----------------
SUELO_SECO = 4095      # lectura con la sonda en el aire      -> 0 %
SUELO_AGUA = 1515      # lectura con la sonda sumergida       -> 100 %

# ---------------- Reglas de control (guia del examen) ----------------
T_LIMITE_BAJO = 28     # T < 28 C              -> LED verde al 30 %
T_LIMITE_MEDIO = 35    # 28 <= T < 35 C        -> LED verde al 70 %
T_LIMITE_ALTO = 40     # 35 <= T < 40 C        -> LED verde al 100 %;  T >= 40 C -> LED rojo
T_VENTILADOR_ON = 35   # el ventilador enciende cuando T >= 35 C ...
T_VENTILADOR_OFF = 32  # ... y solo se apaga cuando T < 32 C (histeresis)
HUMEDAD_BAJA = 30      # ambiente < 30 %  Y  suelo < 30 %   -> LED blanco fijo
HUMEDAD_ALTA = 70      # ambiente >= 70 % O  suelo >= 70 %  -> LED blanco parpadeando

# ---------------- Tiempos, en milisegundos ----------------
PARPADEO_MS = 500           # LED blanco
ENVIO_MS = 15000            # transmision al backend
LECTURA_SENSORES_MS = 2000  # cada cuanto se miden los sensores
ANTIRREBOTE_MS = 50         # pulsador
PRIMERA_LECTURA_MS = 300    # al encender: espera corta para que el HTU21D termine su primera medicion

# ---------------- Comunicacion con el backend (guia, seccion 6) ----------------
# La red WiFi y la IP del servidor van en secretos.py (no se sube a GitHub).
RUTA_LECTURAS = "/api/lecturas"   # endpoint del backend que recibe el JSON (sin token, NOTA 4)
WIFI_REINTENTO_MS = 10000         # sin WiFi, se vuelve a intentar cada 10 s
HTTP_TIMEOUT_S = 3                # espera maxima de la respuesta del servidor, en segundos

# ---------------- Simulacion (mientras no haya HTU21D) ----------------
# El HTU21D del montaje esta danado. Con SIMULAR_AMBIENTE = True, la temperatura
# y la humedad ambiente se simulan con una rampa que sube y baja, para poder
# probar todas las reglas de control. EN LA ENTREGA FINAL DEBE QUEDAR EN False
# (cuando llegue el sensor nuevo, solo se cambia esta linea y se vuelve a subir config.py).
SIMULAR_AMBIENTE = True
SIM_T_MIN = 24          # grados C al inicio de la rampa
SIM_T_MAX = 42          # grados C en el punto mas alto
SIM_H_MIN = 20          # % de humedad ambiente al inicio
SIM_H_MAX = 80          # % en el punto mas alto
SIM_PERIODO_MS = 60000  # una subida y una bajada completas tardan 60 s
