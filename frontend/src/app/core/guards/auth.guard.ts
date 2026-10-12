import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

/**
 * authGuard - Protege Monitoreo y Dashboard: sin sesion lleva al login y
 * recuerda a que pagina se queria entrar (?volver=/monitoreo).
 */
export const authGuard: CanActivateFn = (_ruta, estado) => {
  if (inject(AuthService).estaAutenticado()) {
    return true;
  }
  return inject(Router).createUrlTree(['/login'], { queryParams: { volver: estado.url } });
};

/** invitadoGuard - Si ya hay sesion, el login no tiene sentido: va directo a Monitoreo. */
export const invitadoGuard: CanActivateFn = () => {
  if (inject(AuthService).estaAutenticado()) {
    return inject(Router).createUrlTree(['/monitoreo']);
  }
  return true;
};
