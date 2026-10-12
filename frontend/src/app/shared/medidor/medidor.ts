import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

/**
 * Medidor - Barra horizontal con el valor actual y marcas en los umbrales.
 *
 *   <app-medidor [valor]="34.5" [minimo]="0" [maximo]="50" [marcas]="[28, 35, 40]" color="..." />
 */
@Component({
  selector: 'app-medidor',
  templateUrl: './medidor.html',
  styleUrl: './medidor.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Medidor {
  readonly valor = input<number | null>(null);
  readonly minimo = input(0);
  readonly maximo = input(100);
  readonly marcas = input<number[]>([]);
  readonly color = input('var(--verde)');

  protected posicion(v: number): number {
    const p = ((v - this.minimo()) / (this.maximo() - this.minimo())) * 100;
    return Math.max(0, Math.min(100, p));
  }

  protected readonly relleno = computed(() => {
    const v = this.valor();
    return v === null ? 0 : this.posicion(v);
  });
}
