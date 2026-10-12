import { HttpErrorResponse } from '@angular/common/http';

import { API_URL } from './config';

/** Convierte un error HTTP en un mensaje claro para mostrar en pantalla. */
export function mensajeError(error: HttpErrorResponse): string {
  if (error.status === 0) {
    return `No se pudo conectar con el servidor (${API_URL}). Revisa que el backend esté corriendo con "python run.py".`;
  }
  return error.error?.mensaje ?? `El servidor respondió con un error (${error.status}).`;
}
