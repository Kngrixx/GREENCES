import { DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { EMPTY, catchError, forkJoin, map, switchMap, timer } from 'rxjs';

import { DASHBOARD_CADA_MS, MINUTOS_PERIODO_INICIAL } from '../../core/config';
import { mensajeError } from '../../core/mensaje-error';
import { MaximoMinimo, Resumen, SerieTemperatura } from '../../core/models/lectura';
import { LecturasService } from '../../core/services/lecturas.service';
import { GraficoTemperatura } from '../../shared/grafico-temperatura/grafico-temperatura';
import { Icono, NombreIcono } from '../../shared/icono/icono';

type ClavePeriodo = '5m' | '1h' | '24h' | 'todo';

interface Periodo {
  clave: ClavePeriodo;
  boton: string; // texto del boton del filtro
  texto: string; // como se nombra el periodo en los titulos
  minutos?: number; // sin minutos = todo el historico
}

interface TarjetaResumen {
  titulo: string;
  icono: NombreIcono;
  clase: string;
  unidad: string;
  datos: MaximoMinimo;
}

/** Segundos del ESP32 entre envios: con ese intervalo cada punto del grafico es una lectura. */
const SEGUNDOS_ENTRE_ENVIOS = 15;

/**
 * Dashboard - Informacion historica de un periodo (5 min, 1 h, 24 h o todo):
 *  - Tres tarjetas con el maximo y el minimo de temperatura, humedad ambiente
 *    y humedad del suelo (GET /api/lecturas/resumen?minutos=N).
 *  - Grafico de linea de la temperatura del mismo periodo
 *    (GET /api/lecturas/temperatura?minutos=N).
 * Abre en los ultimos 5 minutos (lo que pide la guia). El filtro cambia las
 * tarjetas y el grafico a la vez. Todo se actualiza solo cada 5 s.
 */
@Component({
  selector: 'app-dashboard',
  imports: [DecimalPipe, DatePipe, Icono, GraficoTemperatura],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Dashboard {
  private readonly lecturas = inject(LecturasService);

  protected readonly cadaSegundos = DASHBOARD_CADA_MS / 1000;
  protected readonly periodos: Periodo[] = [
    { clave: '5m', boton: '5 min', texto: 'últimos 5 minutos', minutos: MINUTOS_PERIODO_INICIAL },
    { clave: '1h', boton: '1 hora', texto: 'última hora', minutos: 60 },
    { clave: '24h', boton: '24 horas', texto: 'últimas 24 horas', minutos: 24 * 60 },
    { clave: 'todo', boton: 'Todo', texto: 'todo el histórico' },
  ];

  /** Periodo elegido en el filtro. */
  protected readonly periodo = signal<ClavePeriodo>('5m');
  /** Periodo de los datos que se ven (cambia cuando llega la respuesta del nuevo periodo). */
  private readonly periodoDatos = signal<ClavePeriodo>('5m');

  protected readonly resumen = signal<Resumen | null>(null);
  protected readonly serie = signal<SerieTemperatura | null>(null);
  protected readonly actualizado = signal<Date | null>(null);
  protected readonly error = signal<string | null>(null);

  protected readonly tarjetas = computed<TarjetaResumen[]>(() => {
    const r = this.resumen();
    const vacio: MaximoMinimo = { maximo: null, minimo: null };
    return [
      { titulo: 'Temperatura', icono: 'termometro', clase: 'temperatura', unidad: '°C', datos: r?.temperatura ?? vacio },
      { titulo: 'Humedad ambiente', icono: 'gota', clase: 'humedad', unidad: '%', datos: r?.humedad_ambiente ?? vacio },
      { titulo: 'Humedad del sustrato', icono: 'brote', clase: 'suelo', unidad: '%', datos: r?.humedad_suelo ?? vacio },
    ];
  });

  /** "últimos 5 minutos", "última hora"... para titulos y notas. */
  protected readonly textoPeriodo = computed(() => this.buscar(this.periodoDatos()).texto);

  /** Ventana del grafico segun el reloj del servidor: [desde, hasta]. */
  protected readonly hasta = computed(() => {
    const s = this.serie();
    return s ? Date.parse(s.hasta) : Date.now();
  });
  protected readonly desde = computed(() => {
    const s = this.serie();
    return s?.desde ? Date.parse(s.desde) : this.hasta() - MINUTOS_PERIODO_INICIAL * 60_000;
  });

  /** Segundos que representa cada punto: 15 = un envio; mas = promedio de ese intervalo. */
  protected readonly intervalo = computed(() => this.serie()?.intervalo_s ?? SEGUNDOS_ENTRE_ENVIOS);
  protected readonly agrupado = computed(() => this.intervalo() > SEGUNDOS_ENTRE_ENVIOS);
  protected readonly descripcionPuntos = computed(() =>
    this.agrupado()
      ? `Cada punto es el promedio de las lecturas de ${duracion(this.intervalo())}.`
      : 'Cada punto es un envío del ESP32 (cada 15 s).',
  );

  protected readonly ultimaTemperatura = computed(() => {
    const puntos = this.serie()?.puntos ?? [];
    return puntos.length ? puntos[puntos.length - 1].temperatura : null;
  });

  constructor() {
    // Cada vez que cambia el periodo se reinicia el temporizador: consulta de
    // inmediato y luego cada 5 s. forkJoin pide las dos rutas en paralelo y
    // switchMap descarta las respuestas del periodo anterior.
    toObservable(this.periodo)
      .pipe(
        switchMap((clave) => {
          const minutos = this.buscar(clave).minutos;
          return timer(0, DASHBOARD_CADA_MS).pipe(
            switchMap(() =>
              forkJoin({
                resumen: this.lecturas.resumen(minutos),
                serie: this.lecturas.temperatura(minutos),
              }).pipe(
                map((datos) => ({ ...datos, clave })),
                catchError((e: HttpErrorResponse) => {
                  this.error.set(mensajeError(e));
                  return EMPTY;
                }),
              ),
            ),
          );
        }),
        takeUntilDestroyed(),
      )
      .subscribe(({ resumen, serie, clave }) => {
        this.resumen.set(resumen);
        this.serie.set(serie);
        this.periodoDatos.set(clave);
        this.actualizado.set(new Date());
        this.error.set(null);
      });
  }

  private buscar(clave: ClavePeriodo): Periodo {
    return this.periodos.find((p) => p.clave === clave) ?? this.periodos[0];
  }
}

/** 300 -> "5 min", 5400 -> "1,5 h", 45 -> "45 s" */
function duracion(segundos: number): string {
  if (segundos < 60) return `${segundos} s`;
  if (segundos < 3600) return `${Math.round(segundos / 60)} min`;
  return `${(segundos / 3600).toLocaleString('es-CO', { maximumFractionDigits: 1 })} h`;
}
