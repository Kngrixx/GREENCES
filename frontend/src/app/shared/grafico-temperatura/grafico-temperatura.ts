import { DatePipe, DecimalPipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, computed, input, signal } from '@angular/core';

import { UMBRALES } from '../../core/config';
import { PuntoTemperatura } from '../../core/models/lectura';

interface PuntoXY {
  t: number; // instante en ms
  v: number; // temperatura
  n: number; // lecturas que representa el punto (1 = un envio; mas = promedio)
  x: number; // posicion en el dibujo
  y: number;
}

/**
 * Si entre dos puntos pasan mas de 45 s (con un envio cada 15 s), el ESP32
 * estuvo apagado y la linea se corta. Con puntos promediados el corte es 3
 * intervalos.
 */
const CORTE_MINIMO_MS = 45_000;

/** Pasos posibles entre marcas del eje X, en minutos (de 1 min a 1 semana). */
const PASOS_MIN = [1, 2, 5, 10, 15, 30, 60, 120, 180, 360, 720, 1440, 2880, 10080];
const MAX_MARCAS_X = 8;

/** Con mas puntos que esto no se dibuja un circulo en cada uno (se ve solo la linea). */
const MAX_CIRCULOS = 120;

/**
 * GraficoTemperatura - Grafico de linea dibujado con SVG (sin librerias).
 *
 * Cada lectura se convierte a coordenadas con una regla de tres:
 *   x = margen + (instante - inicio) / (fin - inicio) * ancho_util
 *   y = margen + (1 - (temperatura - minimo) / (maximo - minimo)) * alto_util
 * (en SVG la y crece hacia abajo, por eso el "1 -").
 */
@Component({
  selector: 'app-grafico-temperatura',
  imports: [DecimalPipe, DatePipe],
  templateUrl: './grafico-temperatura.html',
  styleUrl: './grafico-temperatura.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GraficoTemperatura {
  readonly puntos = input.required<PuntoTemperatura[]>();
  readonly desde = input.required<number>(); // inicio de la ventana (ms)
  readonly hasta = input.required<number>(); // fin de la ventana (ms)
  readonly intervalo = input(15); // segundos que representa cada punto (15 = un envio)

  protected readonly ancho = 1000;
  protected readonly alto = 360;
  protected readonly m = { izq: 48, der: 20, arr: 28, aba: 34 };
  protected readonly base = this.alto - this.m.aba;

  /** Punto bajo el mouse (para el recuadro con el valor). */
  protected readonly seleccion = signal<PuntoXY | null>(null);

  private readonly datos = computed(() =>
    this.puntos()
      .map((p) => ({ t: Date.parse(p.fecha), v: p.temperatura, n: p.lecturas ?? 1 }))
      .sort((a, b) => a.t - b.t),
  );

  /** Rango del eje Y: se ajusta a los datos con un margen y valores redondos. */
  protected readonly ejeY = computed(() => {
    const valores = this.datos().map((d) => d.v);
    let min = valores.length ? Math.min(...valores) - 1.5 : 22;
    let max = valores.length ? Math.max(...valores) + 1.5 : 42;
    if (max - min < 8) {
      const centro = (max + min) / 2;
      min = centro - 4;
      max = centro + 4;
    }
    const paso = max - min <= 12 ? 2 : max - min <= 30 ? 5 : 10;
    return { min: Math.floor(min / paso) * paso, max: Math.ceil(max / paso) * paso, paso };
  });

  /** Duracion de la ventana en ms (minimo 1 minuto, para no dividir por cero). */
  private readonly ventana = computed(() => Math.max(this.hasta() - this.desde(), 60_000));

  private x(t: number): number {
    const util = this.ancho - this.m.izq - this.m.der;
    return this.m.izq + ((t - this.desde()) / this.ventana()) * util;
  }

  private y(v: number): number {
    const { min, max } = this.ejeY();
    const util = this.alto - this.m.arr - this.m.aba;
    return this.m.arr + (1 - (v - min) / (max - min)) * util;
  }

  protected readonly puntosXY = computed<PuntoXY[]>(() =>
    this.datos().map((d) => ({ ...d, x: this.x(d.t), y: this.y(d.v) })),
  );

  /** Tramos continuos de la linea, cada uno con su area sombreada debajo. */
  protected readonly tramos = computed(() => {
    const tramos: PuntoXY[][] = [];
    let actual: PuntoXY[] = [];
    const corte = Math.max(CORTE_MINIMO_MS, this.intervalo() * 3000);
    for (const p of this.puntosXY()) {
      if (actual.length && p.t - actual[actual.length - 1].t > corte) {
        tramos.push(actual);
        actual = [];
      }
      actual.push(p);
    }
    if (actual.length) tramos.push(actual);

    return tramos.map((ps) => {
      const linea = ps.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
      const area = `${linea} L${ps[ps.length - 1].x.toFixed(1)} ${this.base} L${ps[0].x.toFixed(1)} ${this.base} Z`;
      return { linea, area, solo: ps.length === 1 };
    });
  });

  protected readonly lineasY = computed(() => {
    const { min, max, paso } = this.ejeY();
    const lineas = [];
    for (let v = min; v <= max + 0.001; v += paso) lineas.push({ v, y: this.y(v) });
    return lineas;
  });

  /**
   * Marcas del eje X. El paso se elige para que queden maximo 8 marcas:
   * 5 min -> cada minuto, 1 h -> cada 10 min, 24 h -> cada 3 h.
   * Las marcas caen en horas redondas de la hora local (Colombia, UTC-5).
   */
  protected readonly ejeX = computed(() => {
    const desde = this.desde();
    const hasta = this.hasta();
    const minutos = this.ventana() / 60_000;
    const pasoMin = PASOS_MIN.find((p) => minutos / p <= MAX_MARCAS_X) ?? PASOS_MIN[PASOS_MIN.length - 1];
    const paso = pasoMin * 60_000;
    const desfase = new Date(desde).getTimezoneOffset() * 60_000; // Colombia: +5 h
    const marcas = [];
    for (let t = Math.ceil((desde - desfase) / paso) * paso + desfase; t <= hasta; t += paso) {
      marcas.push({ t, x: this.x(t) });
    }
    const variosDias = minutos > 26 * 60;
    const formato = !variosDias ? 'HH:mm' : pasoMin >= 1440 ? 'd MMM' : 'd MMM, HH:mm';
    return { marcas, formato };
  });

  /** Circulo en cada punto solo si no son demasiados. */
  protected readonly conCirculos = computed(() => this.puntosXY().length <= MAX_CIRCULOS);

  /** Formato de la hora en el recuadro del mouse. */
  protected readonly formatoCaja = computed(() => {
    if (this.ventana() > 26 * 3_600_000) return 'd MMM, HH:mm';
    return this.intervalo() > 15 ? 'HH:mm' : 'HH:mm:ss';
  });
  protected readonly anchoCaja = 160;

  /** Umbrales de las reglas de control que caen dentro del rango visible. */
  protected readonly umbrales = computed(() => {
    const { min, max } = this.ejeY();
    return [
      { v: UMBRALES.tempBaja, texto: `${UMBRALES.tempBaja} °C · LED verde al 70 %`, clase: 'baja' },
      { v: UMBRALES.tempMedia, texto: `${UMBRALES.tempMedia} °C · enciende el ventilador`, clase: 'media' },
      { v: UMBRALES.tempAlta, texto: `${UMBRALES.tempAlta} °C · alarma (LED rojo)`, clase: 'alta' },
    ]
      .filter((u) => u.v > min && u.v < max)
      .map((u) => ({ ...u, y: this.y(u.v) }));
  });

  protected readonly ultimo = computed(() => {
    const ps = this.puntosXY();
    return ps.length ? ps[ps.length - 1] : null;
  });

  /** Busca el punto mas cercano al mouse (en coordenadas del dibujo). */
  protected mover(evento: MouseEvent, lienzo: Element): void {
    const caja = lienzo.getBoundingClientRect();
    const xDibujo = ((evento.clientX - caja.left) / caja.width) * this.ancho;
    let cercano: PuntoXY | null = null;
    for (const p of this.puntosXY()) {
      if (!cercano || Math.abs(p.x - xDibujo) < Math.abs(cercano.x - xDibujo)) cercano = p;
    }
    this.seleccion.set(cercano && Math.abs(cercano.x - xDibujo) < 40 ? cercano : null);
  }

  /** Posicion del recuadro de la seleccion, sin salirse del dibujo. */
  protected cajaX(p: PuntoXY): number {
    return Math.min(Math.max(p.x - this.anchoCaja / 2, this.m.izq), this.ancho - this.m.der - this.anchoCaja);
  }

  /** Alto del recuadro: una linea mas cuando el punto es un promedio. */
  protected altoCaja(p: PuntoXY): number {
    return p.n > 1 ? 60 : 44;
  }

  protected cajaY(p: PuntoXY): number {
    const alto = this.altoCaja(p) + 14;
    return p.y - alto < this.m.arr ? p.y + 14 : p.y - alto;
  }
}
