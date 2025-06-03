from datetime import datetime

import pendulum


def now_datetime():
    buenos_aires_tz = pendulum.timezone("America/Argentina/Buenos_Aires")
    return datetime.now(buenos_aires_tz)


def is_valid_date_and_time(date, time=None):
    _now = now_datetime()
    if time:
        return date > _now.date() or (date == _now.date() and time > _now.time())
    return date > _now.date()


def is_valid_datetime(_datetime):
    _timezone = pendulum.timezone("America/Argentina/Buenos_Aires")
    _datetime = _timezone.convert(_datetime)
    return _datetime <= now_datetime()
