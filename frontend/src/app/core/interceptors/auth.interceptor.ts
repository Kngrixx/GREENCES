import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { API_URL } from '../config';
import { AuthService } from '../services/auth.service';

/**
 * authInterceptor - Se ejecuta antes de cada peticion HTTP.
 *
 * 1. Si hay sesion, agrega el encabezado Authorization: Bearer <token>.
 * 2. Si el backend responde 401 (token vencido o invalido), cierra la sesion
 *    y lleva al login.
 */
export const authInterceptor: HttpInterceptorFn = (peticion, siguiente) => {
  const auth = inject(AuthService);
  const esApi = peticion.url.startsWith(API_URL);
  const esLogin = peticion.url.endsWith('/auth/login');
  const token = auth.token();

  const conToken =
    token && esApi && !esLogin
      ? peticion.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : peticion;

  return siguiente(conToken).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && esApi && !esLogin) {
        auth.cerrarSesion('vencida');
      }
      return throwError(() => error);
    }),
  );
};
