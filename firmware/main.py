"""
main.py - Data logger + deteccion de anomalias en el borde (ESP32, MicroPython).

Cada SAMPLE_INTERVAL_S segundos:
  1. Lee DHT11 (temp/humedad), LDR (luz) y PIR (movimiento).
  2. Construye el vector de features del modelo y calcula el score de
     Isolation Forest en el propio ESP32.
  3. Envia lectura + score a una hoja de Google Sheets (Apps Script).

Requiere: config.py (ver config.example.py), isolation_forest.py,
if_data.py (o if_data.mpy) y tz.py.
"""

import gc
import time

import dht
import network
import ntptime
import urequests
from machine import ADC, Pin

import config
import if_data
import tz
from isolation_forest import predict

# ---------------- Hardware ----------------
PIN_DHT = 4
PIN_LDR = 34
PIN_PIR = 27

dht_sensor = dht.DHT11(Pin(PIN_DHT))
ldr = ADC(Pin(PIN_LDR))
ldr.atten(ADC.ATTN_11DB)          # rango completo 0-3.3 V -> 0-4095
pir = Pin(PIN_PIR, Pin.IN)

# ---------------- Parametros ----------------
ADC_MAX = 4095
TEMP_MIN_VALID = 10               # el entrenamiento descarta TEMP <= 10 (fallos del DHT11)
NTP_RESYNC_S = 24 * 3600
RETRY_S = 5


# ---------------- Red y hora ----------------
def connect_wifi(timeout_s=20):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    print("Conectando al WiFi...")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    t0 = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), t0) > timeout_s * 1000:
            raise OSError("timeout conectando al WiFi")
        time.sleep_ms(500)
    print("WiFi conectado, IP:", wlan.ifconfig()[0])
    return wlan


def sync_time():
    """Pone el RTC en UTC por NTP. Devuelve True si tuvo exito."""
    try:
        ntptime.settime()
        return True
    except OSError as e:
        print("NTP fallido:", e)
        return False


def time_is_valid():
    return time.localtime()[0] >= 2024    # el RTC arranca en el anio 2000


# ---------------- Sensores y modelo ----------------
def read_sensors():
    dht_sensor.measure()              # puede lanzar OSError
    return {
        "temp": dht_sensor.temperature(),
        "hum": dht_sensor.humidity(),
        "luz": ldr.read(),            # crudo: mayor valor = mas oscuro
        "mov": pir.value(),
    }


def build_features(r, hour):
    """Mismo orden y transformaciones que en el entrenamiento (if_data.FEATURES):
    HORA, TEMP, MOVIMIENTO, HUMEDAD, LUZ (invertida: mayor = mas luz)."""
    return [hour, r["temp"], r["mov"], r["hum"], ADC_MAX - r["luz"]]


def send(params):
    url = config.WEBHOOK_URL + "?" + "&".join(
        "{}={}".format(k, v) for k, v in params.items())
    resp = urequests.get(url)
    try:
        return resp.status_code
    finally:
        resp.close()                  # imprescindible para liberar memoria


# ---------------- Bucle principal ----------------
def main():
    wlan = connect_wifi()
    last_sync = 0
    if sync_time():
        last_sync = time.time()
    print("Modelo cargado: %d arboles, features=%s"
          % (if_data.N_TREES, getattr(if_data, "FEATURES", "?")))

    while True:
        # --- 1. Lectura (un fallo del sensor no debe tocar la red) ---
        try:
            r = read_sensors()
        except OSError as e:
            print("Error de sensor:", e)
            time.sleep(RETRY_S)
            continue

        # --- 2. Inferencia local ---
        params = {"temp": r["temp"], "hum": r["hum"], "luz": r["luz"], "mov": r["mov"]}
        if time_is_valid() and r["temp"] > TEMP_MIN_VALID:
            hour = tz.local_hour(time.localtime(), config.UTC_OFFSET_HOURS)
            score, anomaly = predict(build_features(r, hour))
            params["score"] = "{:.4f}".format(score)
            params["anom"] = int(anomaly)
            if anomaly:
                print("ANOMALIA score=%.4f" % score, r)
        else:
            print("Sin hora valida o lectura invalida: se omite la inferencia")

        # --- 3. Envio ---
        try:
            if not wlan.isconnected():
                wlan = connect_wifi()
            if time.time() - last_sync > NTP_RESYNC_S and sync_time():
                last_sync = time.time()
            print("HTTP", send(params), params)
        except OSError as e:
            print("Error de red:", e)

        gc.collect()
        time.sleep(config.SAMPLE_INTERVAL_S)


main()
