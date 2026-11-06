from datetime import date, datetime, time, timedelta
import math
import random

import pandas as pd

def load_demo_generation_data(start_date: date, end_date: date) -> pd.DataFrame:
    rng = random.Random(31)
    start = datetime.combine(start_date, time.min)
    stop = datetime.combine(end_date + timedelta(days=1), time.min)
    timestamps = pd.date_range(start=start, end=stop, freq="h", inclusive="left", tz="Europe/Istanbul")

    rows = []
    for timestamp in timestamps:
        hour = timestamp.hour
        daylight = max(0.0, math.sin(math.pi * (hour - 6) / 12))
        solar = 0.0 if daylight == 0 else 3200 + 5200 * daylight * rng.uniform(0.72, 1.0)
        wind = 4700 + 1050 * math.sin((hour + timestamp.day * 2) * math.pi / 12) + rng.uniform(-700, 700)
        wind = max(1800.0, wind)
        total = 48000 + 3500 * math.sin((hour - 4) * math.pi / 12) + rng.uniform(-2200, 2200)
        rows.append((timestamp, wind, solar, max(total, wind + solar + 1)))

    return pd.DataFrame(rows, columns=["timestamp", "wind_mwh", "solar_mwh", "total_mwh"])
