"""
prueba_circuito.py - Prueba del montaje de GreenCES, componente por componente.

No es el programa del examen: solo sirve para comprobar que cada cable y cada
componente de la protoboard funciona antes de escribir las clases (Paso 1).
Aqui SI se usa time.sleep() porque es una prueba; el programa final no lo usara.

Como usarlo:
  1. Conecta la Heltec por USB y abre este archivo en Thonny.
  2. Interprete: MicroPython (ESP32), puerto COM de la Heltec.
  3. Run (F5) y responde en la consola con s / n.
  4. Al final sale un RESUMEN: copialo y pegalo en el chat.
"""
import sys
import time
from machine import Pin, PWM, ADC, I2C

# ---------------- Pines (los mismos del README) ----------------
PIN_PULSADOR = 2
PIN_LED_VERDE = 6      # PWM
PIN_LED_ROJO = 7
PIN_LED_BLANCO = 5
PIN_RELE = 3           # va a la base de Q1 (2N2222A) por R4 de 1 kOhm
PIN_SUELO = 4          # AO del YL-38 -> ADC1_CH3
PIN_SDA = 41
PIN_SCL = 42
DIR_HTU21D = 0x40      # direccion I2C del HTU21D

# Calibracion del YL-69 (medida el 2026-10-10)
SUELO_SECO = 4095      # sonda en el aire
SUELO_AGUA = 1515      # sonda sumergida hasta el tope

resultados = {}        # nombre de la prueba -> texto con OK / FALLA


# ---------------- Utilidades ----------------
def preguntar(texto):
    """Pregunta de si/no en la consola. Devuelve True si la respuesta es s."""
    while True:
        r = input(texto + " (s/n): ").strip().lower()
        if r in ("s", "si", "y"):
            return True
        if r in ("n", "no"):
            return False
        print("   Responde s o n.")


def esperar_enter(texto):
    input(texto + "  [Enter para seguir] ")


def anotar(nombre, ok, detalle=""):
    resultados[nombre] = ("OK" if ok else "FALLA") + ((" - " + detalle) if detalle else "")
    print("   ->", nombre + ":", resultados[nombre])


def porcentaje_a_duty(p):
    """0-100 % -> 0-65535, que es lo que recibe duty_u16()."""
    return int(p * 65535 / 100)


def humedad_suelo(lectura):
    """Convierte la lectura del ADC a % con la calibracion medida (limitada a 0-100)."""
    h = (SUELO_SECO - lectura) * 100 / (SUELO_SECO - SUELO_AGUA)
    return max(0, min(100, h))


# ---------------- Salidas: todo arranca apagado ----------------
led_rojo = Pin(PIN_LED_ROJO, Pin.OUT, value=0)
led_blanco = Pin(PIN_LED_BLANCO, Pin.OUT, value=0)
led_verde = PWM(Pin(PIN_LED_VERDE), freq=1000)
led_verde.duty_u16(0)
rele = Pin(PIN_RELE, Pin.OUT, value=0)    # 0 = Q1 abierto = rele apagado


def apagar_todo():
    led_rojo.value(0)
    led_blanco.value(0)
    led_verde.duty_u16(0)
    rele.value(0)


# ---------------- 1. LEDs ----------------
def prueba_led_rojo():
    print("\n[LED rojo - GPIO7] Se enciende 2 segundos...")
    led_rojo.value(1)
    time.sleep(2)
    led_rojo.value(0)
    anotar("LED rojo", preguntar("   Se encendio el LED rojo?"))


def prueba_led_blanco():
    print("\n[LED blanco - GPIO5] Fijo 2 s y luego parpadea 4 veces cada 500 ms...")
    led_blanco.value(1)
    time.sleep(2)
    for _ in range(8):
        led_blanco.value(not led_blanco.value())
        time.sleep_ms(500)
    led_blanco.value(0)
    anotar("LED blanco", preguntar("   Se encendio fijo y despues parpadeo?"))


def prueba_led_verde():
    print("\n[LED verde - GPIO6, PWM] 30 %, 70 % y 100 %, 2 s cada uno...")
    for p in (30, 70, 100):
        led_verde.duty_u16(porcentaje_a_duty(p))
        print("   PWM al", p, "%  (duty_u16 =", porcentaje_a_duty(p), ")")
        time.sleep(2)
    led_verde.duty_u16(0)
    anotar("LED verde PWM", preguntar("   Viste el brillo subir (30 % se ve tenue)?"))


# ---------------- 2. Pulsador ----------------
def prueba_pulsador():
    print("\n[Pulsador - GPIO2 con PULL_UP]")
    boton = Pin(PIN_PULSADOR, Pin.IN, Pin.PULL_UP)
    inicial = boton.value()
    print("   Valor con el boton suelto:", inicial, "(debe ser 1)")
    if inicial == 0:
        anotar("Pulsador", False, "lee 0 sin presionar: gira el pulsador 90 grados o revisa que GPIO2 no este a GND")
        return
    print("   Presiona el pulsador 3 veces en los proximos 10 segundos...")
    presiones = 0
    anterior = 1
    ultimo_cambio = time.ticks_ms()
    inicio = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), inicio) < 10000 and presiones < 3:
        actual = boton.value()
        ahora = time.ticks_ms()
        # flanco de bajada (1 -> 0) con 50 ms de antirrebote
        if actual != anterior and time.ticks_diff(ahora, ultimo_cambio) > 50:
            ultimo_cambio = ahora
            if actual == 0:
                presiones += 1
                print("   Presion", presiones)
            anterior = actual
        time.sleep_ms(5)
    anotar("Pulsador", presiones >= 3, "detecto %d de 3 presiones" % presiones)


# ---------------- 3. HTU21D (I2C) ----------------
def crc8_htu(datos):
    """CRC del HTU21D (polinomio x^8 + x^5 + x^4 + 1)."""
    crc = 0
    for b in datos:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x131) if (crc & 0x80) else (crc << 1)
    return crc & 0xFF


def leer_crudo(i2c, comando, espera_ms):
    i2c.writeto(DIR_HTU21D, bytes([comando]))
    time.sleep_ms(espera_ms)
    d = i2c.readfrom(DIR_HTU21D, 3)
    if crc8_htu(d[:2]) != d[2]:
        raise ValueError("CRC incorrecto")
    return ((d[0] << 8) | d[1]) & 0xFFFC


def leer_htu(i2c):
    t = -46.85 + 175.72 * leer_crudo(i2c, 0xF3, 60) / 65536
    h = -6 + 125 * leer_crudo(i2c, 0xF5, 25) / 65536
    return t, h


def prueba_htu21d():
    print("\n[HTU21D - I2C SDA=GPIO41, SCL=GPIO42]")
    i2c = I2C(0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=100000)
    encontrados = i2c.scan()
    print("   Dispositivos I2C encontrados:", [hex(x) for x in encontrados])
    if DIR_HTU21D not in encontrados:
        anotar("HTU21D", False, "no aparece 0x40: usa las opciones 8 y 9 del menu para diagnosticar")
        return
    try:
        i2c.writeto(DIR_HTU21D, b"\xfe")    # reinicio por software
        time.sleep_ms(20)
        t, h = leer_htu(i2c)
    except Exception as e:
        anotar("HTU21D", False, "responde pero falla la lectura: " + str(e))
        return
    print("   Temperatura: %.1f C   Humedad: %.1f %%" % (t, h))
    if not (-10 < t < 60 and 0 <= h <= 100):
        anotar("HTU21D", False, "valores fuera de rango (T=%.1f, H=%.1f)" % (t, h))
        return
    print("   Ahora echale el aliento al sensor durante 10 s (la humedad debe subir)...")
    h_max = h
    for _ in range(10):
        time.sleep(1)
        t2, h2 = leer_htu(i2c)
        h_max = max(h_max, h2)
        print("   T = %.1f C   H = %.1f %%" % (t2, h2))
    subio = h_max - h
    anotar("HTU21D", subio >= 3, "T=%.1f C, H=%.1f %%, al soplar subio %.1f puntos" % (t, h, subio))


# ---------------- 4. YL-69 (ADC) ----------------
def promedio_adc(adc, n=30):
    total = 0
    for _ in range(n):
        total += adc.read()
        time.sleep_ms(10)
    return total // n


def prueba_yl69():
    print("\n[YL-69 / YL-38 - AO en GPIO4, ADC de 12 bits]")
    adc = ADC(Pin(PIN_SUELO))
    adc.atten(ADC.ATTN_11DB)          # rango completo de 0 a ~3,1 V
    esperar_enter("   Deja la sonda SECA, en el aire.")
    seco = promedio_adc(adc)
    print("   Seco:", seco, "de 4095  ->  %.0f %% de humedad" % humedad_suelo(seco))
    esperar_enter("   Ahora mete la sonda en agua hasta el tope de las patas.")
    mojado = promedio_adc(adc)
    print("   En agua:", mojado, "de 4095  ->  %.0f %% de humedad" % humedad_suelo(mojado))
    diferencia = abs(seco - mojado)
    anotar("YL-69", diferencia > 500,
           "seco=%d (%.0f %%), agua=%d (%.0f %%)" % (seco, humedad_suelo(seco), mojado, humedad_suelo(mojado)))


# ---------------- 5. Rele (por Q1) + ventilador ----------------
def prueba_rele():
    print("\n[Rele - GPIO3 -> R4 1k -> Q1 2N2222A -> IN del rele; ventilador en NO]")
    rele.value(0)
    print("   GPIO3 = 0 durante 3 s...")
    time.sleep(3)
    con_0 = preguntar("   Hizo clic el rele / se prendio su LED verde / giro el ventilador?")
    rele.value(1)
    print("   GPIO3 = 1 durante 3 s...")
    time.sleep(3)
    con_1 = preguntar("   Y ahora: hizo clic / se prendio el LED verde / giro el ventilador?")
    rele.value(0)

    if con_1 and not con_0:
        anotar("Rele", True, "1 = encendido (Q1 funcionando)")
    elif con_0 and not con_1:
        anotar("Rele", False, "se activa con 0: el IN parece ir directo al GPIO3, debe ir al colector de Q1 (J33)")
    elif con_0 and con_1:
        anotar("Rele", False, "queda activado siempre: pon 10 kOhm (o 1 kOhm) entre IN y +5V, o revisa Q1 en corto")
    else:
        anotar("Rele", False, "no reacciona: revisa R4 (E32-F32), Q1 (E-B-C en H31-H33), emisor a GND y IN en J33")
    if resultados["Rele"].startswith("OK") and not preguntar("   El ventilador giro cuando el rele se activo?"):
        resultados["Rele"] += " | ventilador NO giro: revisa COM a +5V, NO a J55, rojo en H55 y negro en H59"


# ---------------- Diagnostico del I2C ----------------
def escanear_i2c():
    """Busca dispositivos I2C con SDA/SCL normales y cruzados."""
    print("\n[Escaneo I2C en los dos ordenes]")
    for sda, scl in ((PIN_SDA, PIN_SCL), (PIN_SCL, PIN_SDA)):
        i2c = I2C(0, sda=Pin(sda), scl=Pin(scl), freq=100000)
        print("   SDA", sda, "SCL", scl, "->", [hex(d) for d in i2c.scan()])
    print("   Si 0x40 sale en la segunda linea: SDA y SCL estan cruzados en la protoboard.")


def alternar_sda_scl():
    """Pone GPIO41 y GPIO42 en 0/1 alternados para medir con el multimetro en el modulo."""
    print("\n[Alternar SDA/SCL] Mide en los pines SDA y SCL del modulo: deben cambiar entre 0 y 3,3 V")
    sda = Pin(PIN_SDA, Pin.OUT)
    scl = Pin(PIN_SCL, Pin.OUT)
    for i in range(10):
        sda.value(i % 2)
        scl.value((i + 1) % 2)
        print("   GPIO41 (SDA) =", i % 2, "  GPIO42 (SCL) =", (i + 1) % 2)
        time.sleep(2)


# ---------------- Menu ----------------
PRUEBAS = [
    ("LED rojo", prueba_led_rojo),
    ("LED blanco", prueba_led_blanco),
    ("LED verde PWM", prueba_led_verde),
    ("Pulsador", prueba_pulsador),
    ("HTU21D", prueba_htu21d),
    ("YL-69", prueba_yl69),
    ("Rele", prueba_rele),
]
DIAGNOSTICOS = [
    ("Escanear I2C (SDA/SCL normales y cruzados)", escanear_i2c),
    ("Alternar SDA/SCL para medir con el multimetro", alternar_sda_scl),
]


def resumen():
    print("\n================ RESUMEN ================")
    for nombre, _ in PRUEBAS:
        print("%-14s %s" % (nombre, resultados.get(nombre, "sin probar")))
    print("=========================================")


def main():
    print("Prueba del circuito GreenCES")
    print("MicroPython:", sys.implementation.version, "-", sys.platform)
    while True:
        print("\nPruebas:")
        for i, (nombre, _) in enumerate(PRUEBAS, 1):
            print("  %d. %s" % (i, nombre))
        print("Diagnostico del HTU21D:")
        for i, (nombre, _) in enumerate(DIAGNOSTICOS, len(PRUEBAS) + 1):
            print("  %d. %s" % (i, nombre))
        print("  t. Todas las pruebas, en orden")
        print("  r. Ver resumen")
        print("  q. Salir")
        op = input("Elige: ").strip().lower()
        try:
            if op == "t":
                for _, f in PRUEBAS:
                    f()
                resumen()
            elif op == "r":
                resumen()
            elif op == "q":
                break
            elif op.isdigit() and 1 <= int(op) <= len(PRUEBAS):
                PRUEBAS[int(op) - 1][1]()
            elif op.isdigit() and len(PRUEBAS) < int(op) <= len(PRUEBAS) + len(DIAGNOSTICOS):
                DIAGNOSTICOS[int(op) - len(PRUEBAS) - 1][1]()
            else:
                print("Opcion no valida.")
        finally:
            apagar_todo()
    resumen()


try:
    main()
finally:
    apagar_todo()
