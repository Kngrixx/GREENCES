"""Al importar este paquete se registran todos los modelos (lo necesita Flask-Migrate)."""
from app.models.usuario import Usuario  # noqa: F401
from app.models.lectura import Lectura  # noqa: F401
