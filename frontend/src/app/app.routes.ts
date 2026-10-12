import { Routes } from '@angular/router';

import { authGuard, invitadoGuard } from './core/guards/auth.guard';
import { Plantilla } from './layout/plantilla/plantilla';

/**
 * Rutas de la aplicacion.
 * - /login es publica (y si ya hay sesion, redirige a Monitoreo).
 * - Home es publica: presenta la propuesta GreenCES.
 * - Monitoreo y Dashboard muestran datos del backend: piden sesion (authGuard).
 * Las paginas se cargan solo cuando se visitan (loadComponent).
 */
export const routes: Routes = [
  {
    path: 'login',
    canActivate: [invitadoGuard],
    loadComponent: () => import('./pages/login/login').then((m) => m.Login),
    title: 'Iniciar sesión · GreenCES',
  },
  {
    path: '',
    component: Plantilla, // menu superior + pie de pagina
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'home' },
      {
        path: 'home',
        loadComponent: () => import('./pages/home/home').then((m) => m.Home),
        title: 'GreenCES · Monitoreo y ventilación inteligente',
      },
      {
        path: 'monitoreo',
        canActivate: [authGuard],
        loadComponent: () => import('./pages/monitoreo/monitoreo').then((m) => m.Monitoreo),
        title: 'Monitoreo · GreenCES',
      },
      {
        path: 'dashboard',
        canActivate: [authGuard],
        loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.Dashboard),
        title: 'Dashboard · GreenCES',
      },
    ],
  },
  { path: '**', redirectTo: 'home' },
];
