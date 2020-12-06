#  Pyghotess, fast image-PDF OCR Processing
#     Copyright (C) 2020    Pieterjan Montens
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
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
