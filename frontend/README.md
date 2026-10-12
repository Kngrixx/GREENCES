# frontend/

Aplicación web de GreenCES en **Angular 21** (componentes standalone, signals y SCSS). Tiene un menú con tres secciones y un login con token JWT.

| Sección | Ruta | Qué muestra | Datos |
| --- | --- | --- | --- |
| Home | `/home` | Presentación de GreenCES como propuesta de producto: variables, reglas de control, arquitectura y hardware | No usa el backend (es pública) |
| Monitoreo | `/monitoreo` | Valores de los sensores y estado de los LEDs y del ventilador en tiempo real | `GET /api/lecturas/ultima` cada 3 s |
| Dashboard | `/dashboard` | Tres tarjetas con máximos y mínimos, y un gráfico de la temperatura. Un filtro elige el periodo de los dos: 5 min (al abrir), 1 hora, 24 horas o todo | `GET /api/lecturas/resumen?minutos=N` y `GET /api/lecturas/temperatura?minutos=N` cada 5 s |
| Login | `/login` | Inicio de sesión. Los usuarios se crean desde Postman | `POST /api/auth/login` |

Monitoreo y Dashboard piden sesión. Sin token, el guard lleva al login y después regresa a la página que se quería abrir.

## Cómo ejecutarlo

Necesita el backend corriendo (`python run.py` en `backend/`).

```
cd "C:\Users\Usuario\Desktop\Examen 3\frontend"
npm install          (solo la primera vez: descarga node_modules)
ng serve -o
```

Se abre en `http://localhost:4200`. Para entrar se usa el usuario creado en Postman.

## Estructura

```
src/
├── styles.scss                 # estilo global "Laboratorio limpio": colores, botones, chips
└── app/
    ├── app.ts / app.config.ts  # componente raíz y proveedores (router, HttpClient + interceptor, formato es-CO)
    ├── app.routes.ts           # rutas y qué rutas protege el guard
    ├── core/
    │   ├── config.ts           # URL del backend, intervalos de consulta y umbrales de las reglas
    │   ├── models/             # tipos de los datos (Lectura, Resumen, Usuario...)
    │   ├── services/           # AuthService (login, token) y LecturasService (consultas)
    │   ├── interceptors/       # agrega "Authorization: Bearer <token>" y maneja el 401
    │   └── guards/             # authGuard (pide sesión) e invitadoGuard (login)
    ├── layout/plantilla/       # menú superior con las tres secciones y pie de página
    ├── pages/                  # login, home, monitoreo, dashboard
    └── shared/                 # gráfico SVG, medidor, iconos y textos de estado
```

## Cómo funciona por dentro

- **Login y token.**
  1. `AuthService.login()` envía email y contraseña al backend.
  2. El backend devuelve un token JWT, que se guarda en `localStorage`. Así la sesión sobrevive a recargar la página.
  3. `authInterceptor` agrega el token a cada petición.
  4. Si el backend responde **401** (token vencido o inválido), el interceptor cierra la sesión y lleva al login con el aviso "Tu sesión venció".
- **Tiempo real.** Monitoreo y Dashboard consultan el backend con `timer` de RxJS:
  - La primera consulta es inmediata y luego se repite cada 3 o 5 s.
  - `switchMap` descarta una consulta lenta si ya toca la siguiente.
  - `takeUntilDestroyed` detiene las consultas al salir de la página.
  - Los datos se guardan en *signals*, y Angular redibuja solo lo que cambió.
- **Sistema apagado.** Cuando el sistema está APAGADO, el ESP32 no envía datos. El backend responde `en_linea: false` si la última lectura tiene más de 20 s. En ese caso la página lo avisa y muestra atenuados los últimos valores recibidos.
- **Gráfico.** Es un SVG propio, sin librerías. Cada lectura se convierte en coordenadas con una regla de tres:
  - La hora va al eje X y la temperatura al eje Y.
  - Las líneas punteadas son los umbrales de las reglas de control (28, 35 y 40 °C).
  - Si el ESP32 dejó de enviar más de 45 s, la línea se corta para no unir datos que no existen.
- **Filtro de periodo del Dashboard.** Un solo filtro (5 min, 1 hora, 24 horas, Todo) cambia las tarjetas y el gráfico a la vez. Abre en 5 min, que es lo que pide la guía. Al cambiarlo, `switchMap` reinicia el temporizador con el nuevo periodo y descarta las respuestas del anterior.
  - En 5 min y 1 hora cada punto es un envío del ESP32.
  - En 24 horas y Todo, cada punto es el promedio de un intervalo (lo calcula el backend), y el recuadro del mouse dice cuántas lecturas se promediaron.
  - Las marcas del eje X se ajustan al periodo: cada minuto, cada 10 min, cada 3 h o cada 12 h.
- **Dirección del backend.** Se arma con el mismo host de la página (`http://<host>:5000/api`). Si se abre desde otro equipo con la IP del servidor, hay dos cosas que hacer:
  - Ejecutar `ng serve --host 0.0.0.0`.
  - Agregar ese origen, por ejemplo `http://192.168.128.5:4200`, a `CORS_ALLOWED_ORIGINS` en `backend/.env`.
