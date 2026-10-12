import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { Icono } from '../../shared/icono/icono';

/**
 * Plantilla - Estructura comun de las paginas: menu superior con las tres
 * secciones (Home, Monitoreo, Dashboard), la pagina actual y el pie.
 */
@Component({
  selector: 'app-plantilla',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icono],
  templateUrl: './plantilla.html',
  styleUrl: './plantilla.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Plantilla {
  protected readonly auth = inject(AuthService);
  protected readonly anio = new Date().getFullYear();

  protected readonly secciones = [
    { ruta: '/home', texto: 'Home' },
    { ruta: '/monitoreo', texto: 'Monitoreo' },
    { ruta: '/dashboard', texto: 'Dashboard' },
  ];

  protected cerrarSesion(): void {
    this.auth.cerrarSesion();
  }
}
