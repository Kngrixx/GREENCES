import { ChangeDetectionStrategy, Component, input } from '@angular/core';

export type NombreIcono =
  | 'hoja'
  | 'termometro'
  | 'gota'
  | 'brote'
  | 'ventilador'
  | 'foco'
  | 'chip'
  | 'wifi'
  | 'base-datos'
  | 'pantalla'
  | 'grafica'
  | 'candado'
  | 'reloj'
  | 'alerta'
  | 'usuario'
  | 'salir'
  | 'flecha'
  | 'subir'
  | 'bajar'
  | 'pulsador';

/**
 * Icono - Iconos de linea dibujados con SVG dentro del proyecto (no dependen de
 * internet ni de librerias externas). Toman el color del texto (currentColor).
 *
 *   <app-icono nombre="termometro" [tamano]="22" />
 */
@Component({
  selector: 'app-icono',
  templateUrl: './icono.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { 'aria-hidden': 'true', style: 'display: inline-flex; flex-shrink: 0' },
})
export class Icono {
  readonly nombre = input.required<NombreIcono>();
  readonly tamano = input(20);
}
