import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { API_URL } from '../../core/config';
import { AuthService } from '../../core/services/auth.service';
import { Icono } from '../../shared/icono/icono';

/**
 * Login - Formulario de inicio de sesion. Los usuarios se crean desde Postman
 * (POST /api/auth/registro); aqui solo se inicia sesion.
 */
@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink, Icono],
  templateUrl: './login.html',
  styleUrl: './login.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly ruta = inject(ActivatedRoute);

  protected readonly formulario = inject(NonNullableFormBuilder).group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  protected readonly enviando = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly verClave = signal(false);
  /** ?motivo=vencida cuando el interceptor cerro la sesion por un 401. */
  protected readonly sesionVencida = this.ruta.snapshot.queryParamMap.get('motivo') === 'vencida';

  protected entrar(): void {
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      return;
    }
    const { email, password } = this.formulario.getRawValue();
    this.enviando.set(true);
    this.error.set(null);

    this.auth.login(email, password).subscribe({
      next: () => {
        // Vuelve a la pagina que se queria abrir antes del login, o a Monitoreo.
        const volver = this.ruta.snapshot.queryParamMap.get('volver') ?? '/monitoreo';
        this.router.navigateByUrl(volver);
      },
      error: (respuesta: HttpErrorResponse) => {
        this.enviando.set(false);
        this.error.set(mensajeDeError(respuesta));
      },
    });
  }
}

function mensajeDeError(respuesta: HttpErrorResponse): string {
  if (respuesta.status === 0) {
    return `No se pudo conectar con el servidor (${API_URL}). Revisa que el backend esté corriendo con "python run.py".`;
  }
  return respuesta.error?.mensaje ?? 'No se pudo iniciar sesión. Intenta de nuevo.';
}
