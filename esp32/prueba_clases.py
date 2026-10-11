"""
prueba_clases.py - Prueba rapida de las clases del Paso 1.1 (no es el programa final).

Antes de correrla, sube a la placa config.py, hardware.py y htu21d.py
(en Thonny: clic derecho sobre cada archivo -> "Subir a /").

Durante 20 segundos:
  - el LED blanco parpadea cada 500 ms,
  - el LED verde cambia de intensidad cada 2 s (0, 30, 70, 100 %),
  - cada pulsacion alterna el LED rojo y el rele,
  - cada segundo se imprimen las lecturas de los sensores.
Todo con time.ticks_ms(), sin time.sleep(): asi se ve que nada se bloquea.
"""
import time
from machine import I2C, Pin
import config
from hardware import SalidaDigital, SalidaPWM, EntradaDigital, SenalAnaloga
from htu21d import HTU21D

led_rojo = SalidaDigital(config.PIN_LED_ROJO)
led_blanco = SalidaDigital(config.PIN_LED_BLANCO)
led_verde = SalidaPWM(config.PIN_LED_VERDE)
rele = SalidaDigital(config.PIN_RELE)
pulsador = EntradaDigital(config.PIN_PULSADOR, config.ANTIRREBOTE_MS)
suelo = SenalAnaloga(config.PIN_SUELO, config.SUELO_SECO, config.SUELO_AGUA)
i2c = I2C(0, sda=Pin(config.PIN_SDA), scl=Pin(config.PIN_SCL), freq=100000)
htu = HTU21D(i2c, config.LECTURA_SENSORES_MS)

print("HTU21D disponible:", htu.disponible)
print("Prueba de 20 s. Presiona el pulsador para alternar el LED rojo y el rele.")

niveles = [0, 30, 70, 100]
indice = 0
inicio = t_parpadeo = t_nivel = t_imprimir = time.ticks_ms()

while time.ticks_diff(time.ticks_ms(), inicio) < 20000:
    ahora = time.ticks_ms()

    if time.ticks_diff(ahora, t_parpadeo) >= config.PARPADEO_MS:
        led_blanco.toggle()
        t_parpadeo = ahora

    if time.ticks_diff(ahora, t_nivel) >= 2000:
        indice = (indice + 1) % len(niveles)
        led_verde.escribir(niveles[indice])
        t_nivel = ahora

    if pulsador.fue_presionado():
        led_rojo.toggle()
        rele.toggle()
        print("Pulsacion -> LED rojo:", led_rojo.estado(), " rele:", rele.estado())

    htu.actualizar()

    if time.ticks_diff(ahora, t_imprimir) >= 1000:
        print("Suelo: %d (%.2f V) = %.0f %%  |  T: %s C  H: %s %%  |  LED verde: %d %%" % (
            suelo.leer_valor(), suelo.leer_voltaje(), suelo.leer_porcentaje(),
            htu.leer_temperatura(), htu.leer_humedad(), led_verde.porcentaje()))
        t_imprimir = ahora

for salida in (led_rojo, led_blanco, rele):
    salida.apagar()
led_verde.escribir(0)
print("Fin de la prueba: todo apagado.")
