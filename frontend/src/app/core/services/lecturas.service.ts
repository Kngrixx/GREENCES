import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_URL } from '../config';
import { RespuestaUltima, Resumen, SerieTemperatura } from '../models/lectura';

/**
 * LecturasService - Consultas al backend sobre las lecturas del ESP32.
 * Todas estas rutas estan protegidas: el interceptor agrega el token.
 */
@Injectable({ providedIn: 'root' })
export class LecturasService {
  private readonly http = inject(HttpClient);

  /** Ultima lectura y si el sistema esta en linea (Monitoreo). */
  ultima(): Observable<RespuestaUltima> {
    return this.http.get<RespuestaUltima>(`${API_URL}/lecturas/ultima`);
  }

  /** Maximos y minimos (tarjetas del Dashboard). Sin minutos: todo el historico. */
  resumen(minutos?: number): Observable<Resumen> {
    return this.http.get<Resumen>(`${API_URL}/lecturas/resumen`, { params: periodo(minutos) });
  }

  /** Temperaturas del periodo (grafico del Dashboard). Sin minutos: todo el historico. */
  temperatura(minutos?: number): Observable<SerieTemperatura> {
    return this.http.get<SerieTemperatura>(`${API_URL}/lecturas/temperatura`, { params: periodo(minutos) });
  }
}

/** ?minutos=N para un periodo; sin parametros para todo el historico. */
function periodo(minutos?: number): HttpParams {
  return minutos ? new HttpParams().set('minutos', minutos) : new HttpParams();
}
