"""
htu21d.py - Sensor de temperatura y humedad HTU21D (tambien sirve con Si7021 y SHT21).

El sensor tarda unos milisegundos en medir. En vez de quedarse esperando con
time.sleep(), la clase mide por etapas: en cada vuelta del ciclo principal se
llama actualizar(), que pide la medicion, revisa si ya paso el tiempo necesario
y recoge el resultado. Asi el programa sigue atendiendo el pulsador y los LEDs.

Si el sensor no responde (desconectado o danado), temperatura y humedad quedan
en None y la clase lo vuelve a buscar en el siguiente periodo.
"""
import time

DIRECCION = 0x40
CMD_TEMPERATURA = 0xF3        # medir temperatura sin retener el bus I2C
CMD_HUMEDAD = 0xF5            # medir humedad sin retener el bus I2C
CMD_REINICIO = 0xFE
ESPERA_TEMPERATURA_MS = 60    # la hoja de datos da maximo 50 ms
ESPERA_HUMEDAD_MS = 20        # la hoja de datos da maximo 16 ms

# Etapas de la medicion
ESPERANDO = 0
MIDIENDO_T = 1
MIDIENDO_H = 2


def _crc8(datos):
    """CRC del sensor (polinomio x^8 + x^5 + x^4 + 1): detecta datos danados en el bus."""
    crc = 0
    for byte in datos:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x131) if (crc & 0x80) else (crc << 1)
    return crc & 0xFF


class HTU21D:

    def __init__(self, i2c, periodo_ms=2000):
        self._i2c = i2c
        self._periodo_ms = periodo_ms
        self._etapa = ESPERANDO
        # La primera medicion arranca 100 ms despues de crear el objeto.
        self._t_etapa = time.ticks_add(time.ticks_ms(), 100 - periodo_ms)
        self.temperatura = None       # grados C; None mientras no haya lectura
        self.humedad = None           # %
        self.disponible = False
        self._buscar()

    def _buscar(self):
        """Revisa si el sensor responde en el bus y, si responde, lo reinicia."""
        try:
            self.disponible = DIRECCION in self._i2c.scan()
            if self.disponible:
                self._i2c.writeto(DIRECCION, bytes([CMD_REINICIO]))
        except OSError:
            self.disponible = False
        return self.disponible

    def _leer_resultado(self):
        """Lee los 3 bytes de la medicion (MSB, LSB, CRC) y devuelve el valor crudo."""
        datos = self._i2c.readfrom(DIRECCION, 3)
        if _crc8(datos[:2]) != datos[2]:
            raise ValueError("CRC incorrecto")
        return ((datos[0] << 8) | datos[1]) & 0xFFFC   # los 2 bits bajos son de estado

    def actualizar(self):
        """Avanza la medicion una etapa. Se llama en cada vuelta del ciclo principal."""
        ahora = time.ticks_ms()
        transcurrido = time.ticks_diff(ahora, self._t_etapa)
        try:
            if self._etapa == ESPERANDO:
                if transcurrido >= self._periodo_ms:
                    if not self.disponible and not self._buscar():
                        self._t_etapa = ahora          # se reintenta en el siguiente periodo
                        return
                    self._i2c.writeto(DIRECCION, bytes([CMD_TEMPERATURA]))
                    self._etapa, self._t_etapa = MIDIENDO_T, ahora

            elif self._etapa == MIDIENDO_T:
                if transcurrido >= ESPERA_TEMPERATURA_MS:
                    crudo = self._leer_resultado()
                    self.temperatura = round(-46.85 + 175.72 * crudo / 65536, 1)
                    self._i2c.writeto(DIRECCION, bytes([CMD_HUMEDAD]))
                    self._etapa, self._t_etapa = MIDIENDO_H, ahora

            elif self._etapa == MIDIENDO_H:
                if transcurrido >= ESPERA_HUMEDAD_MS:
                    crudo = self._leer_resultado()
                    humedad = -6 + 125 * crudo / 65536
                    self.humedad = round(max(0.0, min(100.0, humedad)), 1)
                    self._etapa, self._t_etapa = ESPERANDO, ahora

        except (OSError, ValueError):
            # El sensor no respondio o llego un dato danado.
            self.disponible = False
            self.temperatura = None
            self.humedad = None
            self._etapa, self._t_etapa = ESPERANDO, ahora

    def reiniciar(self):
        """Olvida la ultima medicion y empieza una nueva de inmediato.

        main.py lo llama al ENCENDER el sistema: asi la primera lectura es nueva
        y no un valor que quedo guardado de antes de apagar.
        """
        self.temperatura = None
        self.humedad = None
        self._etapa = ESPERANDO
        self._t_etapa = time.ticks_add(time.ticks_ms(), -self._periodo_ms)

    def leer_temperatura(self):
        """Ultima temperatura medida en grados C, o None si no hay lectura."""
        return self.temperatura

    def leer_humedad(self):
        """Ultima humedad ambiente medida en %, o None si no hay lectura."""
        return self.humedad
