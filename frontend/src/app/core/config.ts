/**
 * config.ts - Configuracion del frontend.
 */

/**
 * Direccion del backend. Se arma con el mismo host desde el que se abrio la
 * pagina: en el computador del servidor es "localhost"; si la pagina se abre
 * desde otro equipo usando la IP del servidor, apunta a esa misma IP.
 * El backend (Flask) escucha en el puerto 5000.
 */
export const API_URL = `http://${window.location.hostname}:5000/api`;

/** Cada cuanto se consulta la ultima lectura en Monitoreo (el ESP32 envia cada 15 s). */
export const MONITOREO_CADA_MS = 3000;

/** Cada cuanto se actualizan las tarjetas y el grafico del Dashboard. */
export const DASHBOARD_CADA_MS = 5000;

/**
 * Periodo con el que abre el Dashboard, en minutos: los ultimos 5 minutos, que
 * es lo que pide la guia para el grafico. El filtro permite 1 h, 24 h o todo.
 */
export const MINUTOS_PERIODO_INICIAL = 5;

/** Los mismos umbrales que usa el ESP32 (esp32/config.py), para explicar cada estado. */
export const UMBRALES = {
  tempBaja: 28, // T < 28 -> LED verde 30 %
  tempMedia: 35, // 28 <= T < 35 -> 70 %; T >= 35 -> ventilador
  tempAlta: 40, // T >= 40 -> LED rojo
  ventiladorApaga: 32, // el ventilador se apaga cuando T < 32 (histeresis)
  humedadBaja: 30, // ambas < 30 -> LED blanco fijo
  humedadAlta: 70, // alguna >= 70 -> LED blanco parpadeando
} as const;
