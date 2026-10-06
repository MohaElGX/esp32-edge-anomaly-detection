# ESP32 EDGE ANOMALY DETECTION
## Introducción
Este proyecto comienza en Agosto de 2026, como una propuesta de detección de anomalías a partir de datos obtenidos por los sensores del ESP32, para ello se usaron los siguientes sensores:

- Sensor de temperatura y humedad DHT11.
- Sensor de movimiento HC SR501 PIR.
- Sensor de luminosidad DollaTek Digital Light Intensity Sensor.
- Además del timestamp, que lo genera el propio Google Apps Script al insertar la fila.
  
Para el desarrollo de este objetivo se tuvo que implementar un sistema de aprendizaje no supervisado, que se detallará más adelante.

##  Proceso
Para comenzar con este proyecto se tuvo que aprender a manejar los componentes electrónicos del ESP32, así como las conexiones, entradas salidas, módulos, conexión a internet, voltajes, librerías para el manejo de estos componentes, conexiones con Google Drive para empaquetar los datos y mandarlos a un Google Sheet para poder mantener el sistema funcionando de forma constante sin necesidad de conectarse por cable o wifi a un ordenador siempre encendido. 
Una vez entendidas estas bases se procedió con el montaje y testing de los módulos individuales, ante lo cual surgieron diversos problemas:

- El módulo **HC-SR501-PIR** estaba desregulado, la sensibilidad del sensor hacía que se activase con mínimos movimientos, o el otro extremo, el movimiento debía de ser muy continuo y sostenido para que el ciclo de actualización recogiese eso como movimiento, lo cual tomó días de datos para comprobar si la tendencia era constante, resultando en la eliminación de una semana de datos por estar sobre representados los 1 o los 0 en la columna de movimiento, pudiendo resultar en un mal entrenamiento. Para solucionarlo se tuvo que manualmente desatornillar el regulador del sensor para ajustar su sensibilidad.
- Google Sheet no permitía crear un documento que actuase como base de datos por tener varias sesiones abiertas, su solución ampliamente conocida fue abrir una pestaña en modo incógnito e iniciar sesión ahí, tras eso como el microcontrolador ESP32 no tiene la capacidad de gestionar fácilmente la autenticación OAuth2 compleja de Google, establecimos un Webhook HTTP utilizando Google Apps Script como puente de comunicación con un sencillo código de JavaScript basado en La función doGet(e), que captura los parámetros pasados en la URL de la petición HTTP, extrae las lecturas y las escribe con un sheet.appendRow().
- Se optó por comprar una powerbank no inteligente, es decir, que con consumos bajos (como el del ESP32) no se apague automáticamente para ahorrar batería, tras esto se descubrió que la capacidad anunciada no se traduce directamente a energía usable (calor, conversión de voltaje, resistencia interna de las celdas), lo que reduce drásticamente el tiempo de vida útil del Powerbank, apagando el ESP32 en cuestión de días. La solución fue cambiar la fuente de Powerbank a enchufe de pared, pues el ESP32 estará estático durante todo el proceso.
- Al desconectar el ESP32 o apagarse por factores externos, este devuelve valores incoherentes (Filas a 0) antes de quedar totalmente apagado, denominado efecto Brownout, datos que luego cribaremos.

Tras recopilar datos durante 13 días, con varias caídas durante horas por los problemas mencionados, se importó la tabla completa en el Notebook de Jupyter y se comenzó con el análisi y depuración de los datos.
### Procesado, Representación, Limpieza y Conversión de los datos
Para la depuración de los datos primero se tuvo que representarlos, para ello se usaron varias configuraciones y covarianzas.

La representación de la temperatura fue un indicador claro para determinar los valores donde el Brownout hizo efecto, y cribar cuando la temperatura es menor de 10 grados.

El % de filas con el flag de Movimiento a 1 y la representación gráfica fue útil para detectar el primer problema mencionado y ajustar la sensibilidad del sensor, además de calcular la covarianza entre ambas variables para descubrir si existe una relación entre la luz y el movimiento, resultando en 0.038831, pero debemos tener en cuenta que son datos con rangos muy distintos, así que para mayor precisión usaremos el **Test t de Student**, tras el cual, esta vez si, concluimos que existe una dependencia real entre la luz y el movimiento.

Enntonces: Cuando el sensor PIR detecta movimiento (1), el nivel de luz en la estancia es significativamente mayor que cuando no hay movimiento (0).
La presencia de personas suele ir acompañada de encendido de luces, apertura de persianas o interacción con dispositivos.




