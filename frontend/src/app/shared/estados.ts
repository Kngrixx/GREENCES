import { UMBRALES } from '../core/config';
import { ModoLedBlanco } from '../core/models/lectura';

/**
 * estados.ts - Traduce los valores de una lectura a textos y colores.
 * Usa los mismos umbrales que las reglas del ESP32, asi la pagina explica
 * por que cada LED o el ventilador esta como esta.
 */
export type Tono = 'ok' | 'info' | 'alerta' | 'critico' | 'apagado';

export interface Estado {
  texto: string;
  tono: Tono;
}

const SIN_DATO: Estado = { texto: 'Sin dato', tono: 'apagado' };

export function estadoTemperatura(t: number | null): Estado {
  if (t === null) return SIN_DATO;
  if (t < UMBRALES.tempBaja) return { texto: 'Óptima', tono: 'ok' };
  if (t < UMBRALES.tempMedia) return { texto: 'Moderada', tono: 'info' };
  if (t < UMBRALES.tempAlta) return { texto: 'Alta · ventilando', tono: 'alerta' };
  return { texto: 'Crítica', tono: 'critico' };
}

export function estadoHumedad(h: number | null): Estado {
  if (h === null) return SIN_DATO;
  if (h < UMBRALES.humedadBaja) return { texto: 'Baja', tono: 'alerta' };
  if (h < UMBRALES.humedadAlta) return { texto: 'Normal', tono: 'ok' };
  return { texto: 'Alta', tono: 'alerta' };
}

export function motivoLedVerde(pwm: number): string {
  switch (pwm) {
    case 30:
      return `T < ${UMBRALES.tempBaja} °C`;
    case 70:
      return `${UMBRALES.tempBaja} °C ≤ T < ${UMBRALES.tempMedia} °C`;
    case 100:
      return `${UMBRALES.tempMedia} °C ≤ T < ${UMBRALES.tempAlta} °C`;
    default:
      return `T ≥ ${UMBRALES.tempAlta} °C (o sin dato de temperatura)`;
  }
}

export function motivoLedRojo(encendido: boolean): string {
  return encendido ? `Alarma: T ≥ ${UMBRALES.tempAlta} °C` : `Se enciende si T ≥ ${UMBRALES.tempAlta} °C`;
}

export const TEXTO_LED_BLANCO: Record<ModoLedBlanco, string> = {
  0: 'Apagado',
  1: 'Encendido fijo',
  2: 'Parpadeando',
};

export function motivoLedBlanco(modo: ModoLedBlanco): string {
  switch (modo) {
    case 1:
      return `Ambas humedades < ${UMBRALES.humedadBaja} %`;
    case 2:
      return `Alguna humedad ≥ ${UMBRALES.humedadAlta} %`;
    default:
      return 'Humedades en rango intermedio';
  }
}

export function motivoVentilador(encendido: boolean): string {
  return encendido
    ? `Encendió con T ≥ ${UMBRALES.tempMedia} °C; se apaga cuando T < ${UMBRALES.ventiladorApaga} °C`
    : `Se enciende cuando T ≥ ${UMBRALES.tempMedia} °C`;
}

/** "hace 5 s", "hace 3 min", "hace 2 h" */
export function haceCuanto(segundos: number): string {
  const s = Math.max(0, Math.round(segundos));
  if (s < 60) return `hace ${s} s`;
  const minutos = Math.floor(s / 60);
  if (minutos < 60) return `hace ${minutos} min`;
  const horas = Math.floor(minutos / 60);
  if (horas < 48) return `hace ${horas} h`;
  return `hace ${Math.floor(horas / 24)} días`;
}
