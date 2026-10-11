"""
lectura.py - Tabla "lecturas": cada JSON que envia el ESP32 queda como una fila.

Las columnas tienen los mismos nombres que las claves del JSON del ESP32.
La fecha la pone el backend al guardar (el ESP32 no tiene reloj real).

Ademas de validar en el controlador, la base de datos tiene restricciones CHECK:
si algun dato fuera de rango llegara a pasar, PostgreSQL lo rechaza igual.
"""
from app.common.fechas import ahora_utc
from app.extensions import db


class Lectura(db.Model):
    __tablename__ = "lecturas"
    __table_args__ = (
        db.CheckConstraint("sistema IN ('ON', 'OFF')", name="ck_lecturas_sistema"),
        db.CheckConstraint("humedad_ambiente BETWEEN 0 AND 100", name="ck_lecturas_humedad_ambiente"),
        db.CheckConstraint("humedad_suelo BETWEEN 0 AND 100", name="ck_lecturas_humedad_suelo"),
        db.CheckConstraint("led_verde_pwm IN (0, 30, 70, 100)", name="ck_lecturas_led_verde_pwm"),
        db.CheckConstraint("led_rojo IN (0, 1)", name="ck_lecturas_led_rojo"),
        db.CheckConstraint("led_blanco IN (0, 1, 2)", name="ck_lecturas_led_blanco"),
        db.CheckConstraint("ventilador IN (0, 1)", name="ck_lecturas_ventilador"),
    )

    id = db.Column(db.Integer, primary_key=True)
    sistema = db.Column(db.String(3), nullable=False)                 # "ON" / "OFF"
    temperatura = db.Column(db.Float, nullable=True)                  # grados C; null si el HTU21D no responde
    humedad_ambiente = db.Column(db.Float, nullable=True)             # %; null si el HTU21D no responde
    humedad_suelo = db.Column(db.Float, nullable=False)               # % (YL-69)
    led_verde_pwm = db.Column(db.SmallInteger, nullable=False)        # 0, 30, 70 o 100
    led_rojo = db.Column(db.SmallInteger, nullable=False)             # 0 / 1
    led_blanco = db.Column(db.SmallInteger, nullable=False)           # 0 apagado / 1 fijo / 2 parpadeo
    ventilador = db.Column(db.SmallInteger, nullable=False)           # 0 / 1
    # index=True: el Dashboard busca por fecha (ultimos 5 minutos); el indice lo hace rapido.
    fecha = db.Column(db.DateTime(timezone=True), nullable=False, default=ahora_utc, index=True)
