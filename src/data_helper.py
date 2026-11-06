from datetime import date

import pandas as pd

def load_generation_data(start_date: date, end_date: date) -> pd.DataFrame:
    return pd.DataFrame(
        columns=["timestamp", "wind_mwh", "solar_mwh", "total_mwh"]
    )
