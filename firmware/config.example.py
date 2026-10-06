# Copia este archivo como `config.py`, rellenalo y subelo al ESP32.
# `config.py` esta en .gitignore: NUNCA lo subas al repositorio.

WIFI_SSID = "tu_ssid"
WIFI_PASSWORD = "tu_password"

# URL de despliegue de tu Google Apps Script (termina en /exec)
WEBHOOK_URL = "https://script.google.com/macros/s/XXXXXXXXXXXX/exec"

UTC_OFFSET_HOURS = 1       # hora estandar de Espana; el horario de verano es automatico
SAMPLE_INTERVAL_S = 60     # segundos entre muestras
