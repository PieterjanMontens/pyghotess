from datetime import datetime
import pytz
import math


def starttime_get():
    return datetime.now(pytz.utc)


def status_get(start_time, version, counter):
    now = datetime.now(pytz.utc)
    delta = now - start_time
    delta_s = math.floor(delta.total_seconds())
    return {
        'all_systems': 'nominal',
        'id': __name__,
        'timestamp': str(now),
        'online_since': str(start_time),
        'online_for_seconds': delta_s,
        'api_version': version,
        'api_counter': counter,
    }
