import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, catchError, interval, switchMap, timer } from 'rxjs';

import { MONITOREO_CADA_MS, UMBRALES } from '../../core/config';
import { mensajeError } from '../../core/mensaje-error';
import { RespuestaUltima } from '../../core/models/lectura';
import { LecturasService } from '../../core/services/lecturas.service';
import {
  TEXTO_LED_BLANCO,
  estadoHumedad,
  estadoTemperatura,
  haceCuanto,
  motivoLedBlanco,
  motivoLedRojo,
  motivoLedVerde,
  motivoVentilador,
} from '../../shared/estados';
import { Icono } from '../../shared/icono/icono';
import { Medidor } from '../../shared/medidor/medidor';

/**
 * Monitoreo - Valores de los sensores y estado de los LEDs y del ventilador en
 * tiempo real. Consulta GET /api/lecturas/ultima cada 3 s (el ESP32 envia
 * cada 15 s, asi un dato nuevo aparece en pantalla en maximo 3 s).
 */
@Component({
  selector: 'app-monitoreo',
  imports: [DecimalPipe, DatePipe, Icono, Medidor],
  templateUrl: './monitoreo.html',
  styleUrl: './monitoreo.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Monitoreo {
  private readonly lecturas = inject(LecturasService);

  protected readonly u = UMBRALES;
  protected readonly cadaSegundos = MONITOREO_CADA_MS / 1000;

  private readonly respuesta = signal<RespuestaUltima | null>(null);
  private readonly recibidaEn = signal(0); // momento en que llego la respuesta (ms)
  private readonly ahora = signal(Date.now()); // reloj que avanza cada segundo
  protected readonly error = signal<string | null>(null);

  protected readonly cargando = computed(() => this.respuesta() === null && this.error() === null);
  protected readonly lectura = computed(() => this.respuesta()?.lectura ?? null);
  protected readonly enLinea = computed(() => this.respuesta()?.en_linea ?? false);

  /** Segundos desde la ultima lectura, sumando lo que ha pasado desde la consulta. */
  protected readonly segundos = computed(() => {
    const r = this.respuesta();
    if (r?.segundos_desde_ultima == null) return null;
    return r.segundos_desde_ultima + (this.ahora() - this.recibidaEn()) / 1000;
  });
  protected readonly hace = computed(() => {
    const s = this.segundos();
    return s === null ? '' : haceCuanto(s);
  });

  // Estados y explicaciones de cada tarjeta
  protected readonly estadoT = computed(() => estadoTemperatura(this.lectura()?.temperatura ?? null));
  protected readonly estadoHA = computed(() => estadoHumedad(this.lectura()?.humedad_ambiente ?? null));
  protected readonly estadoHS = computed(() => estadoHumedad(this.lectura()?.humedad_suelo ?? null));
  protected readonly textoLedBlanco = TEXTO_LED_BLANCO;
  protected readonly motivoLedVerde = motivoLedVerde;
  protected readonly motivoLedRojo = motivoLedRojo;
  protected readonly motivoLedBlanco = motivoLedBlanco;
  protected readonly motivoVentilador = motivoVentilador;

  constructor() {
    // Consulta inmediata y luego cada 3 s. switchMap descarta una consulta lenta
    // si ya toca la siguiente; takeUntilDestroyed la detiene al salir de la pagina.
    timer(0, MONITOREO_CADA_MS)
      .pipe(
        switchMap(() =>
          this.lecturas.ultima().pipe(
            catchError((e: HttpErrorResponse) => {
              this.error.set(mensajeError(e));
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((r) => {
        this.respuesta.set(r);
        this.recibidaEn.set(Date.now());
        this.error.set(null);
      });

    interval(1000)
      .pipe(takeUntilDestroyed())
      .subscribe(() => this.ahora.set(Date.now()));
  }
}
