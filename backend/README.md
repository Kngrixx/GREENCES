# backend/

API en Flask que recibe las lecturas del ESP32, las guarda en PostgreSQL y se las entrega al frontend. Tiene login con token JWT, y todas las rutas de consulta están protegidas.

## Estructura (separación por capas)

```
backend/
├── run.py                  # punto de entrada: python run.py
├── config.py               # configuración (lee el archivo .env)
├── requirements.txt        # librerías con versión fija
├── .env.example            # plantilla de .env (el .env real no se sube a GitHub)
├── migrations/             # creación de tablas (Flask-Migrate / Alembic)
├── postman/                # colección de Postman para probar la API
└── app/
    ├── __init__.py         # create_app(): arma la aplicación, CORS, JWT y rutas
    ├── extensions.py       # db (SQLAlchemy), migrate, jwt
    ├── models/             # tablas: usuario.py (usuarios), lectura.py (lecturas)
    ├── routes/             # URLs y qué rutas piden token
    ├── controllers/        # leen la petición, validan y responden JSON
    ├── services/           # lógica y consultas a la base de datos
    └── common/             # validaciones del JSON del ESP32 y fechas
```

Una petición recorre las capas así: **ruta** → **controlador** → **servicio** → **modelo/base de datos** → respuesta JSON.

## Instalación en Windows (una sola vez)

1. **Crear la base de datos** en pgAdmin: Servers → PostgreSQL → clic derecho en *Databases* → *Create* → *Database…* → nombre `greences` → *Save*.
2. **Crear el entorno virtual e instalar las librerías** (en la consola `cmd`):
   ```
   cd "C:\Users\Usuario\Desktop\Examen 3\backend"
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   En PowerShell, antes de `activate`: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`.
3. **Configurar `.env`**: abrir `backend/.env` y cambiar `TU_CONTRASENA` por la contraseña del usuario `postgres` (la que se puso al instalar PostgreSQL). Si la contraseña tiene símbolos como `@`, `:` o `/`, hay que escribirlos codificados (`@` → `%40`).
4. **Crear las tablas**:
   ```
   flask db upgrade
   ```
   Aplica la migración de `migrations/versions/`, que crea las tablas `usuarios` y `lecturas`. En pgAdmin aparecen en *greences → Schemas → public → Tables*.

## Uso diario

```
cd "C:\Users\Usuario\Desktop\Examen 3\backend"
.venv\Scripts\activate
python run.py
```

El servidor queda en `http://localhost:5000` y, para el ESP32, en `http://IP_DEL_PC:5000`. La consola muestra cada petición; los envíos del ESP32 aparecen como `POST /api/lecturas ... 201` cada 15 s. La primera vez, Windows puede preguntar por el firewall: permitir en **redes privadas**.

## Postman

Importar `postman/GreenCES.postman_collection.json` (*Import* → arrastrar el archivo). La colección trae las variables `base_url` y `token`.

1. **1. Usuarios → Registrar usuario**: crea el usuario. La guía pide que los usuarios se creen desde Postman.
2. **1. Usuarios → Iniciar sesión**: devuelve el token y lo guarda solo en `{{token}}`.
3. **3. Frontend**: estas rutas usan ese token automáticamente (Authorization → Bearer Token).

## Endpoints

Todas las rutas empiezan por `/api`.

| Método | Ruta | Token | Para qué |
| --- | --- | --- | --- |
| GET | `/health` | No | El servidor responde |
| GET | `/health/db` | No | La base de datos responde |
| POST | `/auth/registro` | No | Crear usuario (`nombre_completo`, `email`, `password`, `identificacion`) |
| POST | `/auth/login` | No | Iniciar sesión (`email`, `password`) → `access_token` |
| GET | `/auth/perfil` | Sí | Datos del usuario del token |
| POST | `/lecturas` | **No** | El ESP32 envía su JSON cada 15 s (NOTA 4 de la guía) |
| GET | `/lecturas/ultima` | Sí | Última lectura y si el sistema está en línea (Monitoreo) |
| GET | `/lecturas/resumen?minutos=5` | Sí | Máximos y mínimos de temperatura y humedades (tarjetas del Dashboard). `?minutos=5`, `60` o `1440`; sin el parámetro, todo el histórico |
| GET | `/lecturas/temperatura?minutos=5` | Sí | Temperaturas del periodo (gráfico del Dashboard). Mismo `?minutos=` que el resumen |
| GET | `/lecturas?limite=20` | Sí | Últimas lecturas guardadas |

### Recepción de datos del ESP32 (`POST /api/lecturas`)

Recibe el mismo JSON que imprime el ESP32 (ver el README principal) y lo valida antes de guardarlo:

- Deben venir las 8 claves.
- `sistema` debe ser `"ON"` u `"OFF"`.
- `temperatura` debe estar entre −40 y 125 °C, o ser `null`.
- `humedad_ambiente` debe estar entre 0 y 100, o ser `null`.
- `humedad_suelo` debe estar entre 0 y 100.
- `led_verde_pwm` debe ser 0, 30, 70 o 100.
- `led_rojo` y `ventilador` deben ser 0 o 1.
- `led_blanco` debe ser 0, 1 o 2.

Responde `201` con la lectura guardada, o `400` con la lista de errores. La fecha la pone el servidor al guardar, en UTC. La tabla además tiene restricciones `CHECK` con los mismos rangos.

### Respuestas para el frontend

`GET /api/lecturas/ultima`:

```json
{
  "lectura": { "id": 8, "sistema": "ON", "temperatura": 24.2, "humedad_ambiente": 20.6, "humedad_suelo": 0.0,
               "led_verde_pwm": 30, "led_rojo": 0, "led_blanco": 1, "ventilador": 0,
               "fecha": "2026-10-11T02:53:37.489923+00:00" },
  "en_linea": true,
  "segundos_desde_ultima": 3.2
}
```

`en_linea` es `false` si la última lectura tiene más de 20 s. Pasa cuando el sistema está APAGADO, porque en ese estado el ESP32 no transmite, o cuando está desconectado.

`GET /api/lecturas/resumen`:

```json
{
  "temperatura": { "maximo": 41.8, "minimo": 24.2 },
  "humedad_ambiente": { "maximo": 79.4, "minimo": 20.6 },
  "humedad_suelo": { "maximo": 77.6, "minimo": 0.0 },
  "total_lecturas": 5,
  "minutos": null,
  "desde": null
}
```

Se calcula en PostgreSQL con `MAX` y `MIN`, solo con lecturas del sistema ENCENDIDO. Los `null` se ignoran. Con `?minutos=N` solo cuentan las lecturas de los últimos N minutos.

`GET /api/lecturas/temperatura?minutos=5`:

```json
{ "minutos": 5, "desde": "2026-10-11T02:48:10+00:00", "hasta": "2026-10-11T02:53:10+00:00",
  "intervalo_s": 15,
  "puntos": [ { "fecha": "2026-10-11T02:53:10+00:00", "temperatura": 24.2, "lecturas": 1 } ] }
```

- Hasta 75 minutos (300 envíos), cada lectura es un punto (`intervalo_s` = 15, `lecturas` = 1).
- En periodos más largos (`?minutos=1440` o sin el parámetro = todo el histórico), el periodo se divide en intervalos iguales para que salgan máximo 300 puntos. PostgreSQL agrupa las lecturas de cada intervalo (`GROUP BY`) y devuelve su promedio; `lecturas` dice cuántas se promediaron.
- Sin el parámetro, `desde` es la fecha de la primera lectura.

## Códigos HTTP que usa la API

| Código | Cuándo |
| --- | --- |
| 200 | Consulta correcta |
| 201 | Usuario o lectura creados |
| 400 | Datos incompletos o inválidos |
| 401 | Falta el token, es inválido o venció, o el login es incorrecto |
| 404 | Ruta no encontrada |
| 409 | El email o la identificación ya están registrados |
| 500 | Error de la base de datos |
