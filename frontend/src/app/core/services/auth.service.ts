import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, map, tap } from 'rxjs';

import { API_URL } from '../config';
import { RespuestaLogin, Usuario } from '../models/usuario';

const CLAVE_TOKEN = 'greences.token';
const CLAVE_USUARIO = 'greences.usuario';

/**
 * AuthService - Inicio y cierre de sesion.
 *
 * Al iniciar sesion el backend devuelve un token JWT. Se guarda en localStorage
 * para que la sesion siga activa al recargar la pagina, y el interceptor lo
 * agrega a cada peticion (Authorization: Bearer <token>).
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly tokenActual = signal<string | null>(leer(CLAVE_TOKEN));
  private readonly usuarioActual = signal<Usuario | null>(leerUsuario());

  /** Usuario con sesion iniciada (o null). Se puede usar en las plantillas. */
  readonly usuario = this.usuarioActual.asReadonly();

  /** Primer nombre, para el saludo del menu. */
  readonly nombreCorto = computed(() => this.usuarioActual()?.nombre_completo.split(' ')[0] ?? '');

  token(): string | null {
    return this.tokenActual();
  }

  /** true si hay un token guardado y todavia no vence. */
  estaAutenticado(): boolean {
    const token = this.tokenActual();
    return token !== null && !tokenVencido(token);
  }

  /** POST /api/auth/login. Si las credenciales son correctas, guarda la sesion. */
  login(email: string, password: string): Observable<Usuario> {
    return this.http.post<RespuestaLogin>(`${API_URL}/auth/login`, { email, password }).pipe(
      tap((respuesta) => this.guardarSesion(respuesta.access_token, respuesta.usuario)),
      map((respuesta) => respuesta.usuario),
    );
  }

  /** Borra la sesion y lleva al login. motivo='vencida' muestra un aviso alla. */
  cerrarSesion(motivo?: 'vencida'): void {
    borrar(CLAVE_TOKEN);
    borrar(CLAVE_USUARIO);
    this.tokenActual.set(null);
    this.usuarioActual.set(null);
    this.router.navigate(['/login'], { queryParams: motivo ? { motivo } : {} });
  }

  private guardarSesion(token: string, usuario: Usuario): void {
    escribir(CLAVE_TOKEN, token);
    escribir(CLAVE_USUARIO, JSON.stringify(usuario));
    this.tokenActual.set(token);
    this.usuarioActual.set(usuario);
  }
}

/**
 * Lee la fecha de vencimiento (exp) que trae el token. Un JWT tiene tres partes
 * separadas por puntos; la del medio es un JSON en base64 con los datos.
 */
function tokenVencido(token: string): boolean {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const datos = JSON.parse(atob(base64)) as { exp?: number };
    return datos.exp !== undefined && datos.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

/* localStorage puede fallar (modo privado o almacenamiento bloqueado): se protege con try/catch. */
function leer(clave: string): string | null {
  try {
    return localStorage.getItem(clave);
  } catch {
    return null;
  }
}

function escribir(clave: string, valor: string): void {
  try {
    localStorage.setItem(clave, valor);
  } catch {
    /* sin almacenamiento: la sesion dura solo mientras la pagina este abierta */
  }
}

function borrar(clave: string): void {
  try {
    localStorage.removeItem(clave);
  } catch {
    /* nada que borrar */
  }
}

function leerUsuario(): Usuario | null {
  const texto = leer(CLAVE_USUARIO);
  if (!texto) return null;
  try {
    return JSON.parse(texto) as Usuario;
  } catch {
    return null;
  }
}
