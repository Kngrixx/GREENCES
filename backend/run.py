"""
run.py - Punto de entrada: crea la aplicacion y la pone a escuchar.

    python run.py
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # host="0.0.0.0": escucha en todas las tarjetas de red del computador, no solo
    # en localhost. Asi el ESP32 puede llegar desde el WiFi con la IP del PC.
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PUERTO", "5000")),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
