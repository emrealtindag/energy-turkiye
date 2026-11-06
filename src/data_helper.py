"""EPİAŞ data loading and cleaning.

Kaan's implementation should provide ``load_generation_data`` and return the
columns documented in README.md. Keep credentials out of source control.
"""

from datetime import date

import pandas as pd


def load_generation_data(start_date: date, end_date: date) -> pd.DataFrame:
    """Load hourly generation data for the inclusive date range.

    Replace this placeholder with the EPİAŞ-backed implementation. Returning
    an empty, correctly-shaped frame lets the UI run before integration.
    """
    return pd.DataFrame(
        columns=["timestamp", "wind_mwh", "solar_mwh", "total_mwh"]
    )
