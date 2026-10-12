/**
 * Tipos de los datos que entrega el backend. Las claves son las mismas del
 * JSON que envia el ESP32.
 */
export type EstadoSistema = 'ON' | 'OFF';

/** 0 apagado, 1 encendido fijo, 2 parpadeando */
export type ModoLedBlanco = 0 | 1 | 2;

export interface Lectura {
  id: number;
  sistema: EstadoSistema;
  temperatura: number | null; // null si el HTU21D no responde
  humedad_ambiente: number | null;
  humedad_suelo: number;
  led_verde_pwm: number; // 0, 30, 70 o 100
  led_rojo: 0 | 1;
  led_blanco: ModoLedBlanco;
  ventilador: 0 | 1;
  fecha: string; // ISO 8601 en UTC
}

/** GET /api/lecturas/ultima */
export interface RespuestaUltima {
  lectura: Lectura | null;
  en_linea: boolean;
  segundos_desde_ultima: number | null;
}

export interface MaximoMinimo {
  maximo: number | null;
  minimo: number | null;
}

/** GET /api/lecturas/resumen */
export interface Resumen {
  temperatura: MaximoMinimo;
  humedad_ambiente: MaximoMinimo;
  humedad_suelo: MaximoMinimo;
  total_lecturas: number;
  minutos: number | null; // null = todo el historico
  desde: string | null;
}

export interface PuntoTemperatura {
  fecha: string;
  temperatura: number;
  lecturas: number; // 1 = un envio del ESP32; mas de 1 = promedio de varias lecturas
}

/** GET /api/lecturas/temperatura[?minutos=5] */
export interface SerieTemperatura {
  minutos: number | null; // null = todo el historico
  desde: string | null; // inicio del periodo (null si todavia no hay lecturas)
  hasta: string; // hora del servidor al responder
  intervalo_s: number; // 15 = cada punto es un envio; mas = promedio de ese intervalo
  puntos: PuntoTemperatura[];
}
