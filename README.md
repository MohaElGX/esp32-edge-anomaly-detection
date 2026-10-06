# ESP32 EDGE ANOMALY DETECTION
## Introducción
Este proyecto comienza en Agosto de 2026, como una propuesta de detección de anomalías a partir de datos obtenidos por los sensores del ESP32, para ello se usaron los siguientes sensores:

- Sensor de temperatura y humedad DHT11
- Sensor de movimiento HC SR501 PIR
- Sensor de luminosidad DollaTek Digital Light Intensity Sensor
- Además de obtener la fecha y hora desde Google Drive

Para el desarrollo de este objetivo se tuvo que implementar un sistema de aprendizaje no supervisado, que se detallará más adelante.

##  Proceso
Para comenzar con este proyecto se tuvo que aprender a manejar los componentes electrónicos del ESP32, así como las conexiones, entradas salidas, módulos, conexión a internet, voltajes, librerías para el manejo de estos componentes, conexiones con Google Drive para empaquetar los datos y mandarlos a un Google Sheet para poder mantener el sistema funcionando de forma constante sin necesidad de conectarse por cable o wifi a un ordenador siempre encendido. 
Una vez entendidas estas bases se procedió con el montaje y testing de los módulos individuales, ante lo cual surgieron diversos problemas:

- El módulo **HC-SR501-PIR** estaba desregulado, la sensibilidad del sensor hacía que se activase con mínimos movimientos, o el otro extremo, el movimiento debía de ser muy continuo y sostenido para que el ciclo de actualización recogiese eso como movimiento, lo cual tomó días de datos para comprobar si la tendencia era constante, resultando en la eliminación de una semana de datos por estar sobre representados los 1 o los 0 en la columna de movimiento, pudiendo resultar en un mal entrenamiento. Para solucionarlo se tuvo que manualmente desatornillar el regulador del sensor para ajustar su sensibilidad.
- Google Sheet no permitía crear un documento que actuase como base de datos por tener varias sesiones abiertas, su solución ampliamente conocida fue abrir una pestaña en modo incógnito e iniciar sesión ahí, tras eso como el microcontrolador ESP32 no tiene la capacidad de gestionar fácilmente la autenticación OAuth2 compleja de Google, establecimos un Webhook HTTP utilizando Google Apps Script como puente de comunicación con un sencillo código de JavaScript basado en La función doGet(e), que captura los parámetros pasados en la URL de la petición HTTP, extrae las lecturas y las escribe con un sheet.appendRow().
- Se optó por comprar una powerbank no inteligente, es decir, que con consumos bajos (como el del ESP32) no se apague automáticamente para ahorrar batería, tras esto se descubrió que la capacidad anunciada no se traduce directamente a energía usable (calor, conversión de voltaje, resistencia interna de las celdas), lo que reduce drásticamente el tiempo de vida útil del Powerbank, apagando el ESP32 en cuestión de días. La solución fue cambiar la fuente de Powerbank a enchufe de pared, pues el ESP32 estará estático durante todo el proceso.
