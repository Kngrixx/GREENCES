/** Usuario tal como lo devuelve el backend (sin la contrasena). */
export interface Usuario {
  id: number;
  nombre_completo: string;
  email: string;
  identificacion: string;
}

/** Respuesta de POST /api/auth/login */
export interface RespuestaLogin {
  mensaje: string;
  access_token: string;
  usuario: Usuario;
}
