"""
secretos_ejemplo.py - Plantilla de los datos privados del montaje.

1. Copia este archivo con el nombre secretos.py (en la misma carpeta esp32/).
2. Llena tus datos en secretos.py y subelo a la placa junto con los demas archivos.

secretos.py esta en .gitignore: la clave del WiFi nunca llega a GitHub. Este
archivo de ejemplo si se sube, para que se sepa que datos hay que llenar.
"""

# Red WiFi de 2,4 GHz (el ESP32 no se conecta a redes de 5 GHz).
WIFI_SSID = "nombre_de_la_red"
WIFI_CLAVE = "clave_de_la_red"

# Direccion del computador donde corre el servidor (backend Flask o servidor_prueba.py).
# En Windows se consulta con "ipconfig" -> Direccion IPv4 del adaptador WiFi.
# El ESP32 y ese computador deben estar conectados a la misma red.
SERVIDOR = "http://192.168.1.100:5000"
