"""Compara tz.local_hour con zoneinfo (Europe/Madrid) en todo un anio."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import tz

MADRID = ZoneInfo("Europe/Madrid")


def test_local_hour_matches_zoneinfo():
    t = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2028, 1, 1, tzinfo=timezone.utc)
    while t < end:
        utc = (t.year, t.month, t.day, t.hour, t.minute, t.second, t.weekday(), 0)
        assert tz.local_hour(utc, 1) == t.astimezone(MADRID).hour, t
        t += timedelta(minutes=30)
