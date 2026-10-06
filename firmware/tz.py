"""
tz.py - Hora local de Espana (CET/CEST) a partir de la hora UTC del RTC.

El RTC del ESP32 queda en UTC tras ntptime.settime(). El modelo usa la
HORA local como feature, asi que hay que convertirla. Solo se necesita la
hora (0-23), no la fecha local completa.

Horario de verano UE: del ultimo domingo de marzo 01:00 UTC al ultimo
domingo de octubre 01:00 UTC.
"""

_T = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)


def _dow_sun0(y, m, d):
    """Dia de la semana (algoritmo de Sakamoto): 0 = domingo."""
    if m < 3:
        y -= 1
    return (y + y // 4 - y // 100 + y // 400 + _T[m - 1] + d) % 7


def _last_sunday(y, m):
    """Dia del mes del ultimo domingo (valido para marzo y octubre, 31 dias)."""
    return 31 - _dow_sun0(y, m, 31)


def is_dst_eu(utc):
    """utc: tupla tipo time.localtime() con el RTC en UTC."""
    y, mo, d, h = utc[0], utc[1], utc[2], utc[3]
    if mo < 3 or mo > 10:
        return False
    if 3 < mo < 10:
        return True
    if mo == 3:
        return (d, h) >= (_last_sunday(y, 3), 1)
    return (d, h) < (_last_sunday(y, 10), 1)


def local_hour(utc, std_offset=1):
    """Hora local (0-23). std_offset = desfase UTC en invierno (CET = 1)."""
    return (utc[3] + std_offset + (1 if is_dst_eu(utc) else 0)) % 24
